from eLCS import *
import random
import copy
import math
import numpy as np


class Classifier():
    def __init__(self,elcs,a=None,b=None,c=None,d=None):
        #Major Parameters
        self.specifiedAttList = np.array([],dtype='int64')
        self.conditionType = np.array([]) #0 for discrete, 1 for continuous
        self.conditionDiscrete = np.array([]) #discrete values
        self.conditionContinuous = np.array([]) #continouous values
        self.phenotype = None #arbitrary

        self.fitness = elcs.init_fit
        self.accuracy = 0.0
        self.numerosity = 1
        self.aveMatchSetSize = None
        self.deletionVote = None

        # Experience Management
        self.timeStampGA = None
        self.initTimeStamp = None

        # Classifier Accuracy Tracking --------------------------------------
        self.matchCount = 0  # Known in many LCS implementations as experience i.e. the total number of times this classifier was in a match set
        self.correctCount = 0  # The total number of times this classifier was in a correct set

        if isinstance(c, np.ndarray):
            self.classifierCovering(elcs, a, b, c, d)
        elif isinstance(a, Classifier):
            self.classifierCopy(a, b)

    # Classifier Construction Methods
    def classifierCovering(self, elcs, setSize, exploreIter, state, phenotype):
        # Initialize new classifier parameters----------
        self.timeStampGA = exploreIter
        self.initTimeStamp = exploreIter
        self.aveMatchSetSize = setSize
        dataInfo = elcs.env.formatData

        # -------------------------------------------------------
        # DISCRETE PHENOTYPE
        # -------------------------------------------------------
        if dataInfo.discretePhenotype:
            self.phenotype = phenotype
        # -------------------------------------------------------
        # CONTINUOUS PHENOTYPE
        # -------------------------------------------------------
        else:
            phenotypeRange = dataInfo.phenotypeList[1] - dataInfo.phenotypeList[0]
            rangeRadius = random.randint(25,75) * 0.01 * phenotypeRange / 2.0  # Continuous initialization domain radius.
            Low = float(phenotype) - rangeRadius
            High = float(phenotype) + rangeRadius
            self.phenotype = np.array([Low, High])

        while self.specifiedAttList.size < 1:
            for attRef in range(state.size):
                if random.random() < elcs.p_spec and not(np.isnan(state[attRef])):
                    # print("B",end="")
                    self.specifiedAttList = np.append(self.specifiedAttList, attRef)
                    self.buildMatch(elcs, attRef, state)  # Add classifierConditionElement

    def classifierCopy(self, toCopy, exploreIter):
        self.specifiedAttList = copy.deepcopy(toCopy.specifiedAttList)
        self.conditionType = copy.deepcopy(toCopy.conditionType)
        self.conditionDiscrete = copy.deepcopy(toCopy.conditionDiscrete)
        self.conditionContinuous = copy.deepcopy(toCopy.conditionContinuous)

        self.phenotype = copy.deepcopy(toCopy.phenotype)
        self.timeStampGA = exploreIter
        self.initTimeStamp = exploreIter
        self.aveMatchSetSize = copy.deepcopy(toCopy.aveMatchSetSize)
        self.fitness = toCopy.fitness
        self.accuracy = toCopy.accuracy

    def buildMatch(self, elcs, attRef, state):
        attributeInfoType = elcs.env.formatData.attributeInfoType[attRef]
        if not(attributeInfoType): #Discrete
            attributeInfoValue = elcs.env.formatData.attributeInfoDiscrete[attRef]
        else:
            attributeInfoValue = elcs.env.formatData.attributeInfoContinuous[attRef]

        # Continuous attribute
        if attributeInfoType:
            attRange = attributeInfoValue[1] - attributeInfoValue[0]
            rangeRadius = random.randint(25, 75) * 0.01 * attRange / 2.0  # Continuous initialization domain radius.
            Low = state[attRef] - rangeRadius
            High = state[attRef] + rangeRadius
            condList = np.array([Low, High])

            if np.array_equal(self.conditionContinuous,np.array([])):
                self.conditionContinuous = np.array([condList])
                self.conditionDiscrete = np.array([np.nan])
            else:
                self.conditionContinuous = np.concatenate((self.conditionContinuous,[condList]),axis = 0)
                self.conditionDiscrete = np.concatenate((self.conditionDiscrete, [np.nan]), axis=0)
            self.conditionType = np.append(self.conditionType,1)

        # Discrete attribute
        else:
            condList = state[attRef]

            if np.array_equal(self.conditionContinuous, np.array([])):
                self.conditionContinuous = np.array([[np.nan,np.nan]])
                self.conditionDiscrete = np.array([condList])
            else:
                self.conditionContinuous = np.concatenate((self.conditionContinuous,[[np.nan,np.nan]]))
                self.conditionDiscrete = np.concatenate((self.conditionDiscrete,[condList]),axis=0)
            self.conditionType = np.append(self.conditionType,0)

    # Matching
    def match(self, state, elcs):
        for i in range(self.conditionDiscrete.size):
            attributeInfoType = elcs.env.formatData.attributeInfoType[self.specifiedAttList[i]]
            if not (attributeInfoType):  # Discrete
                attributeInfoValue = elcs.env.formatData.attributeInfoDiscrete[self.specifiedAttList[i]]
            else:
                attributeInfoValue = elcs.env.formatData.attributeInfoContinuous[self.specifiedAttList[i]]

            # Continuous
            if attributeInfoType:
                instanceValue = state[self.specifiedAttList[i]]
                if np.isnan(instanceValue):
                    pass
                elif self.conditionContinuous[i,0] < instanceValue < self.conditionContinuous[i,1]:
                    pass
                else:
                    return False

            # Discrete
            else:
                stateRep = state[self.specifiedAttList[i]]
                if stateRep == self.conditionDiscrete[i] or np.isnan(stateRep):
                    pass
                else:
                    return False
        return True

    def equals(self, elcs, cl):
        phenotypesMatch = False
        if not elcs.env.formatData.discretePhenotype:
            if (cl.phenotype == self.phenotype).all():
                phenotypesMatch = True
        else:
            if cl.phenotype == self.phenotype:
                phenotypesMatch = True

        if phenotypesMatch and cl.specifiedAttList.size == self.specifiedAttList.size:
            clRefs = np.sort(cl.specifiedAttList)
            selfRefs = np.sort(self.specifiedAttList)
            if (clRefs == selfRefs).all():
                for i in range(cl.specifiedAttList.size):
                    tempIndex = np.where(self.specifiedAttList == cl.specifiedAttList[i])[0][0]
                    if not ((cl.conditionType[i] == 1 and self.conditionType[tempIndex] == 1 and cl.conditionContinuous[i,0] == self.conditionContinuous[tempIndex,0] and cl.conditionContinuous[i,1] == self.conditionContinuous[tempIndex,1]) or
                            (cl.conditionType[i] == 0 and self.conditionType[tempIndex] == 0 and cl.conditionDiscrete[i] == self.conditionDiscrete[tempIndex])):
                        return False
                return True
        return False

    def updateNumerosity(self, num):
        """ Updates the numberosity of the classifier.  Notice that 'num' can be negative! """
        self.numerosity += num

    def updateExperience(self):
        """ Increases the experience of the classifier by one. Once an epoch has completed, rule accuracy can't change."""
        self.matchCount += 1

    def updateCorrect(self):
        """ Increases the correct phenotype tracking by one. Once an epoch has completed, rule accuracy can't change."""
        self.correctCount += 1

    def updateMatchSetSize(self, elcs, matchSetSize):
        """  Updates the average match set size. """
        if self.matchCount < 1.0 / elcs.beta:
            self.aveMatchSetSize = (self.aveMatchSetSize * (self.matchCount - 1) + matchSetSize) / float(
                self.matchCount)
        else:
            self.aveMatchSetSize = self.aveMatchSetSize + elcs.beta * (matchSetSize - self.aveMatchSetSize)

    def updateAccuracy(self):
        """ Update the accuracy tracker """
        self.accuracy = self.correctCount / float(self.matchCount)

    def updateFitness(self, elcs):
        """ Update the fitness parameter. """
        if elcs.env.formatData.discretePhenotype or (
                self.phenotype[1] - self.phenotype[0]) / elcs.env.formatData.phenotypeRange < 0.5:
            self.fitness = pow(self.accuracy, elcs.nu)
        else:
            if (self.phenotype[1] - self.phenotype[0]) >= elcs.env.formatData.phenotypeRange:
                self.fitness = 0.0
            else:
                self.fitness = math.fabs(pow(self.accuracy, elcs.nu) - (
                            self.phenotype[1] - self.phenotype[0]) / elcs.env.formatData.phenotypeRange)

    def isSubsumer(self, elcs):
        if self.matchCount > elcs.theta_sub and self.accuracy > elcs.acc_sub:
            return True
        return False

    def isMoreGeneral(self, cl, elcs):
        if self.specifiedAttList.size >= cl.specifiedAttList.size:
            return False
        for i in range(self.specifiedAttList.size):
            attributeInfoType = elcs.env.formatData.attributeInfoType[self.specifiedAttList[i]]
            if self.specifiedAttList[i] not in cl.specifiedAttList:
                return False

            # Continuous
            if attributeInfoType:
                otherRef = np.where(cl.specifiedAttList == self.specifiedAttList[i])[0][0]
                if self.conditionContinuous[i,0] < cl.conditionContinuous[otherRef,0]:
                    return False
                if self.conditionContinuous[i,1] > cl.conditionContinuous[otherRef,1]:
                    return False
        return True

    def uniformCrossover(self, elcs, cl):
        if elcs.env.formatData.discretePhenotype or random.random() < 0.5:
            p_self_specifiedAttList = copy.deepcopy(self.specifiedAttList)
            p_cl_specifiedAttList = copy.deepcopy(cl.specifiedAttList)

            # Make list of attribute references appearing in at least one of the parents.-----------------------------
            comboAttList = np.array([], dtype="int64")
            for i in p_self_specifiedAttList:
                comboAttList = np.append(comboAttList, i)
            for i in p_cl_specifiedAttList:
                if i not in comboAttList:
                    comboAttList = np.append(comboAttList, i)
                elif not elcs.env.formatData.attributeInfoType[i]:
                    index = np.where(comboAttList == i)[0][0]
                    comboAttList = np.delete(comboAttList, index)
            comboAttList = np.sort(comboAttList)

            changed = False
            for attRef in comboAttList:
                attributeInfoType = elcs.env.formatData.attributeInfoType[attRef]
                probability = 0.5
                ref = 0
                if attRef in p_self_specifiedAttList:
                    ref += 1
                if attRef in p_cl_specifiedAttList:
                    ref += 1

                if ref == 0:
                    pass
                elif ref == 1:
                    if attRef in p_self_specifiedAttList and random.random() > probability:
                        i = np.where(self.specifiedAttList == attRef)[0][0]
                        cl.conditionType = np.append(cl.conditionType,self.conditionType[i])
                        cl.conditionDiscrete = np.append(cl.conditionDiscrete,self.conditionDiscrete[i])
                        cl.conditionContinuous = np.concatenate((cl.conditionContinuous,[self.conditionContinuous[i]]),axis=0)
                        self.conditionType = np.delete(self.conditionType,i)
                        self.conditionDiscrete = np.delete(self.conditionDiscrete,i)
                        self.conditionContinuous = np.delete(self.conditionContinuous,i,axis=0)

                        cl.specifiedAttList = np.append(cl.specifiedAttList, attRef)
                        self.specifiedAttList = np.delete(self.specifiedAttList, i)
                        changed = True

                    if attRef in p_cl_specifiedAttList and random.random() < probability:
                        i = np.where(cl.specifiedAttList == attRef)[0][0]
                        self.conditionType = np.append(self.conditionType, cl.conditionType[i])
                        self.conditionDiscrete = np.append(self.conditionDiscrete, cl.conditionDiscrete[i])
                        self.conditionContinuous = np.concatenate(
                            (self.conditionContinuous, [cl.conditionContinuous[i]]), axis=0)
                        cl.conditionType = np.delete(cl.conditionType, i)
                        cl.conditionDiscrete = np.delete(cl.conditionDiscrete, i)
                        cl.conditionContinuous = np.delete(cl.conditionContinuous, i,axis=0)

                        self.specifiedAttList = np.append(self.specifiedAttList, attRef)
                        cl.specifiedAttList = np.delete(cl.specifiedAttList, i)
                        changed = True
                else:
                    # Continuous Attribute
                    if attributeInfoType:
                        i_cl1 = np.where(self.specifiedAttList == attRef)[0][0]
                        i_cl2 = np.where(cl.specifiedAttList == attRef)[0][0]
                        tempKey = random.randint(0, 3)
                        if tempKey == 0:
                            temp = self.conditionContinuous[i_cl1,0]
                            self.conditionContinuous[i_cl1,0] = cl.conditionContinuous[i_cl2,0]
                            cl.conditionContinuous[i_cl2,0] = temp
                        elif tempKey == 1:
                            temp = self.conditionContinuous[i_cl1,1]
                            self.conditionContinuous[i_cl1,1] = cl.conditionContinuous[i_cl2,1]
                            cl.conditionContinuous[i_cl2,1] = temp
                        else:
                            allList = np.concatenate((self.conditionContinuous[i_cl1], cl.conditionContinuous[i_cl2]))
                            newMin = np.amin(allList)
                            newMax = np.amax(allList)
                            if tempKey == 2:
                                self.conditionContinuous[i_cl1] = np.array([newMin, newMax])
                                cl.conditionType = np.delete(cl.conditionType,i_cl2)
                                cl.conditionContinuous = np.delete(cl.conditionContinuous,i_cl2,axis=0)
                                cl.conditionDiscrete = np.delete(cl.conditionDiscrete,i_cl2)

                                a = np.where(cl.specifiedAttList == attRef)[0][0]
                                cl.specifiedAttList = np.delete(cl.specifiedAttList, a)
                            else:
                                cl.conditionContinuous[i_cl2] = np.array([newMin, newMax])
                                self.conditionType = np.delete(self.conditionType, i_cl1)
                                self.conditionContinuous = np.delete(self.conditionContinuous, i_cl1,axis=0)
                                self.conditionDiscrete = np.delete(self.conditionDiscrete, i_cl1)

                                a = np.where(self.specifiedAttList == attRef)[0][0]
                                self.specifiedAttList = np.delete(self.specifiedAttList, a)

                    # Discrete Attribute
                    else:
                        pass

            tempList1 = copy.deepcopy(p_self_specifiedAttList)
            tempList2 = copy.deepcopy(cl.specifiedAttList)
            tempList1 = np.sort(tempList1)
            tempList2 = np.sort(tempList2)

            # if changed:
            # print("CHANGED")
            # print(tempList1)
            # print(tempList2)

            if changed and len(set(tempList1) & set(tempList2)) == tempList2.size:
                # print("PASS")
                changed = False

            return changed
        else:
            return self.phenotypeCrossover(cl)

    def phenotypeCrossover(self, cl):
        changed = False
        if (self.phenotype[0] == cl.phenotype[0] and self.phenotype[1] == cl.phenotype[1]):
            return changed
        else:
            tempKey = random.random() < 0.5  # Make random choice between 4 scenarios, Swap minimums, Swap maximums, Children preserve parent phenotypes.
            if tempKey:  # Swap minimum
                temp = self.phenotype[0]
                self.phenotype[0] = cl.phenotype[0]
                cl.phenotype[0] = temp
                changed = True
            elif tempKey:  # Swap maximum
                temp = self.phenotype[1]
                self.phenotype[1] = cl.phenotype[1]
                cl.phenotype[1] = temp
                changed = True

        return changed

    def Mutation(self, elcs, state, phenotype):
        changed = False
        # Mutate Condition
        for attRef in range(elcs.env.formatData.numAttributes):
            attributeInfoType = elcs.env.formatData.attributeInfoType[attRef]
            if not (attributeInfoType):  # Discrete
                attributeInfoValue = elcs.env.formatData.attributeInfoDiscrete[attRef]
            else:
                attributeInfoValue = elcs.env.formatData.attributeInfoContinuous[attRef]

            if random.random() < elcs.upsilon and not(np.isnan(state[attRef])):
                # Mutation
                if attRef not in self.specifiedAttList:
                    self.specifiedAttList = np.append(self.specifiedAttList, attRef)
                    self.buildMatch(elcs, attRef, state)
                    changed = True
                elif attRef in self.specifiedAttList:
                    i = np.where(self.specifiedAttList == attRef)[0][0]

                    if not attributeInfoType or random.random() > 0.5:
                        self.specifiedAttList = np.delete(self.specifiedAttList, i)
                        self.conditionType = np.delete(self.conditionType,i)
                        self.conditionDiscrete = np.delete(self.conditionDiscrete,i)
                        self.conditionContinuous = np.delete(self.conditionContinuous,i,axis=0)
                        changed = True
                    else:
                        attRange = float(attributeInfoValue[1]) - float(attributeInfoValue[0])
                        mutateRange = random.random() * 0.5 * attRange
                        if random.random() > 0.5:
                            if random.random() > 0.5:
                                self.conditionContinuous[i,0] += mutateRange
                            else:
                                self.conditionContinuous[i,0] -= mutateRange
                        else:
                            if random.random() > 0.5:
                                self.conditionContinuous[i,1] += mutateRange
                            else:
                                self.conditionContinuous[i,1] -= mutateRange
                        self.conditionContinuous[i] = np.sort(self.conditionContinuous[i])
                        changed = True

                else:
                    pass

        # Mutate Phenotype
        if elcs.env.formatData.discretePhenotype:
            nowChanged = self.discretePhenotypeMutation(elcs)
        else:
            nowChanged = self.continuousPhenotypeMutation(elcs, phenotype)

        if changed or nowChanged:
            return True

    def discretePhenotypeMutation(self, elcs):
        changed = False
        if random.random() < elcs.upsilon:
            phenotypeList = copy.deepcopy(elcs.env.formatData.phenotypeList)
            index = np.where(phenotypeList == self.phenotype)
            phenotypeList = np.delete(phenotypeList, index)
            newPhenotype = np.random.choice(phenotypeList)
            self.phenotype = newPhenotype
            changed = True
        return changed

    def continuousPhenotypeMutation(self, elcs, phenotype):
        changed = False
        if random.random() < elcs.upsilon:
            phenRange = self.phenotype[1] - self.phenotype[0]
            mutateRange = random.random() * 0.5 * phenRange
            tempKey = random.randint(0,2)  # Make random choice between 3 scenarios, mutate minimums, mutate maximums, mutate both
            if tempKey == 0:  # Mutate minimum
                if random.random() > 0.5 or self.phenotype[
                    0] + mutateRange <= phenotype:  # Checks that mutated range still contains current phenotype
                    self.phenotype[0] += mutateRange
                else:  # Subtract
                    self.phenotype[0] -= mutateRange
                changed = True
            elif tempKey == 1:  # Mutate maximum
                if random.random() > 0.5 or self.phenotype[
                    1] - mutateRange >= phenotype:  # Checks that mutated range still contains current phenotype
                    self.phenotype[1] -= mutateRange
                else:  # Subtract
                    self.phenotype[1] += mutateRange
                changed = True
            else:  # mutate both
                if random.random() > 0.5 or self.phenotype[
                    0] + mutateRange <= phenotype:  # Checks that mutated range still contains current phenotype
                    self.phenotype[0] += mutateRange
                else:  # Subtract
                    self.phenotype[0] -= mutateRange
                if random.random() > 0.5 or self.phenotype[
                    1] - mutateRange >= phenotype:  # Checks that mutated range still contains current phenotype
                    self.phenotype[1] -= mutateRange
                else:  # Subtract
                    self.phenotype[1] += mutateRange
                changed = True
            self.phenotype = np.sort(self.phenotype)
        return changed

    def updateTimeStamp(self, ts):
        """ Sets the time stamp of the classifier. """
        self.timeStampGA = ts

    def setAccuracy(self, acc):
        """ Sets the accuracy of the classifier """
        self.accuracy = acc

    def setFitness(self, fit):
        """  Sets the fitness of the classifier. """
        self.fitness = fit

    def subsumes(self, elcs, cl):
        # Discrete Phenotype
        if elcs.env.formatData.discretePhenotype:
            if cl.phenotype == self.phenotype:
                if self.isSubsumer(elcs) and self.isMoreGeneral(cl, elcs):
                    return True
            return False

        # Continuous Phenotype
        else:
            if self.phenotype[0] >= cl.phenotype[0] and self.phenotype[1] <= cl.phenotype[1]:
                if self.isSubsumer(elcs) and self.isMoreGeneral(cl, elcs):
                    return True
                return False

    def getDelProp(self, elcs, meanFitness):
        """  Returns the vote for deletion of the classifier. """
        if self.fitness / self.numerosity >= elcs.delta * meanFitness or self.matchCount < elcs.theta_del:
            self.deletionVote = self.aveMatchSetSize * self.numerosity

        elif self.fitness == 0.0:
            self.deletionVote = self.aveMatchSetSize * self.numerosity * meanFitness / (
                        elcs.init_fit / self.numerosity)
        else:
            self.deletionVote = self.aveMatchSetSize * self.numerosity * meanFitness / (
                        self.fitness / self.numerosity)
        return self.deletionVote