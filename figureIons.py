"""
Author: Chris Mitchell (chris.mit7@gmail.com)
Copyright (C) 2012 Chris Mitchell

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import re, masses, operator, copy

class figureIons(object):
    def __init__(self,scan, tolerance, skipLoss=None):
    #def __init__(self,seq,ioncharge,mods, tolerance, skipLoss=None):
        self.sequence=scan.peptide.upper()
        self.ioncharge = scan.charge
        self.modList = {}
        self.scan = scan
        if scan.mods:
            mods = scan.mods
            for mod in mods:
                modification, start, mass, modType = mod
                self.modList[int(start)] = (mass,modType.lower())
            # print self.modList
        self.tolerance = tolerance/1000000.0
        self.skipLoss=skipLoss
        
    def predictPeaks(self):
        """
        returns a list of peaks predicted from a peptide:
        format sorted by low->high mz:
        list of tuples of: [(m/z, fragment type(A,B,C,X,Y,Z), fragment #, charge state,neutral loss, peptide),(...)]
        """
        self.peakTable = set([])
        mass = 0
        modList = self.modList
        maxcharge = int(self.ioncharge)
        hw = masses.mod_weights['h'][0]
        losses = set([(0,('a','b','c','x','y','z'),'')])
        lossMasses = copy.deepcopy(masses.lossMasses)
        if self.skipLoss:
            for aa in self.skipLoss:
                lossMasses[aa] = list(lossMasses[aa])
                for info in self.skipLoss[aa]:
                    lossMasses[aa].remove(info)
                lossMasses[aa] = tuple(lossMasses[aa])
        charge=1#for starting nh3
        sLen=len(self.sequence)
        for i,v in enumerate(self.sequence):
            ionIndex = i+1#1 based for ion reporting -- not used for internal calcs
            try:
                if v in lossMasses:
                    for k in lossMasses[v]:
                        losses.add(k)
            except IndexError:
                pass
            mass+=masses.protein_weights[v][0]
            charge+=masses.protein_weights[v][1]
            try:
                mass+=float(modList[i][0])
#                charge+=masses.mod_weights[modList[i+1]][1]
            except KeyError:
                pass
            if charge>maxcharge:
                charge=maxcharge
            for icharge in xrange(1,charge+1):
                for lossType in losses:
                    lossMass = lossType[0]
                    tcharge = icharge
                    if 0<i<sLen-1 and not lossType[2]:
                        a = (mass-masses.mod_weights['cho'][0]+hw+hw*tcharge)/tcharge
                        tad = (a,'a',ionIndex,tcharge,None,v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    elif 0<i<sLen-1 and 'a' in lossType[1]:
                        a = (mass-masses.mod_weights['cho'][0]+hw+hw*tcharge+lossMass)/tcharge
                        tad = (a,'a',ionIndex,tcharge,lossType[2],v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    if 0<i<sLen-1 and not lossType[2]:
                        b = (mass+masses.mod_weights['h'][0]-hw+hw*tcharge)/tcharge
                        tad = (b,'b',ionIndex,tcharge,None,v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    elif 0<i<sLen-1 and 'b' in lossType[1]:
                        b = (mass+masses.mod_weights['h'][0]-hw+hw*tcharge+lossMass)/tcharge
                        tad = (b,'b',ionIndex,tcharge,lossType[2],v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    if i<sLen-1 and not lossType[2]:
                        c = (mass+masses.mod_weights['nh2'][0]+hw+hw*tcharge)/tcharge
                        tad = (c,'c',ionIndex,tcharge,None,v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    elif i<sLen-1 and 'c' in lossType[1]:
                        c = (mass+masses.mod_weights['nh2'][0]+hw+hw*tcharge+lossMass)/tcharge
                        tad = (c,'c',ionIndex,tcharge,lossType[2],v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
        charge=int(self.ioncharge)-1#for rightmost charge -- we remove the NH3 charge
        losses = set([(0,('a','b','c','x','y','z'),'')])
        mass = 0
        for i,v in enumerate(reversed(self.sequence)):
            mass+=masses.protein_weights[v][0]
            charge+=masses.protein_weights[v][1]
            try:
                mass+=float(modList[i][0])
                #charge+=masses.mod_weights[modList[i+1]][1]
            except KeyError:
                pass
            ionIndex = i+1
            if charge>maxcharge:
                charge=maxcharge
            #we need to look one ahead
            try:
                if v in lossMasses:
                    for k in lossMasses[v]:
                        losses.add(k)
            except IndexError:
                pass
            for icharge in xrange(1,charge+1):
                for lossType in losses:
                    lossMass = lossType[0]
                    tcharge=icharge
                    if not lossType[2]:
                        x = (mass+masses.mod_weights['co'][0]+masses.mod_weights['oh'][0]-hw+hw*tcharge)/tcharge
                        tad = (x,'x',ionIndex,tcharge,None,v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    elif 'x' in lossType[1]:
                        x = (mass+masses.mod_weights['co'][0]+masses.mod_weights['oh'][0]-hw+hw*tcharge+lossMass)/tcharge
                        tad = (x,'x',ionIndex,tcharge,lossType[2],v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    if not lossType[2]:
                        y = (mass+masses.mod_weights['h'][0]+masses.mod_weights['oh'][0]+hw*tcharge)/tcharge
                        tad = (y,'y',ionIndex,tcharge,None,v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    elif 'y' in lossType[1]:
                        y = (mass+masses.mod_weights['h'][0]+masses.mod_weights['oh'][0]+hw*tcharge+lossMass)/tcharge
                        tad = (y,'y',ionIndex,tcharge,lossType[2],v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    if not lossType[2]:
                        z = (mass-masses.mod_weights['nh2'][0]+masses.mod_weights['oh'][0]+hw+hw*tcharge)/tcharge
                        tad = (z,'z',ionIndex,tcharge,None,v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
                    elif 'z' in lossType[1]:
                        z = (mass-masses.mod_weights['nh2'][0]+masses.mod_weights['oh'][0]+hw+hw*tcharge+lossMass)/tcharge
                        tad = (z,'z',ionIndex,tcharge,lossType[2],v)
                        if tad not in self.peakTable:
                            self.peakTable.add(tad)
        for signature, signature_mass in masses.signatureIons.iteritems():
            self.peakTable.add((signature_mass, 'signature', 0, 1, signature, ''))
        self.peakTable = list(self.peakTable)
        self.peakTable.sort(key=operator.itemgetter(0))
        return self.peakTable
    
    def assignPeaks(self):
        """
        given a list of masses, returns what predicted peaks match up
        return format: [((m/z, intensity, amino acid, fragmentation type, fragment #, charge, neutral loss), error)]
        """
        try:
            matchDict = self.scan.matched
            self.x = matchDict['m/z']
            self.y = matchDict['intensity']
            aas = [self.sequence[i] for i in matchDict['start']]
            out = [((i,j,k,l,m,n,o),p) for (i,j,k,l,m,n,o,p) in zip(self.x, self.y, [p[0] for p in matchDict['series']], matchDict['start'],matchDict['charge'],matchDict['losses'],aas,matchDict['error'])]
        except AttributeError:
            self.predictPeaks()
            scan = self.scan
            # mods = scan.getModifications()
            mz = scan.scans
            x = []
            y = []
            for i in mz:
                x.append(float(i[0]))
                y.append(float(i[1]))
            out = []
            start=0
            primaries = set([])
            tol = self.tolerance
            for seqindex,peaks in enumerate(self.peakTable):
                mz,fragType, fragNum,charge,loss,aa = peaks
                candidates = []
                seen = False
                for index,m in enumerate(x[start:]):
                    lower = m*(1+tol)
                    if lower > mz > m*(1-tol):
                        seen = True
                        candidates.append((x[start+index],y[start+index],fragType, fragNum,charge,loss,aa))
                    elif mz > lower and seen:
                        start=index
                        break
                if candidates:
                    candidates.sort(key=operator.itemgetter(1), reverse=True)
                    for toadd in candidates:
                        if (toadd[2] == 'signature' or not toadd[5]) and toadd[1]:
                            primaries.add((toadd[2:5]))
                    #pick the largest peak
                    # print (candidates[0][0]-mz)/(1+tol)
                    # print candidates[0][0],mz,tol
                    out.append((candidates[0],(candidates[0][0]-mz)/mz*1000000))
            #now we filter out our secondary ions if the primary ion is missing 
            #(so we don't have a yn-h20 if we don't have a yn)
            out[:] = [x for x in out if not x[0][5] or (x[0][5] and x[0][2:5] in primaries)]
        return out
