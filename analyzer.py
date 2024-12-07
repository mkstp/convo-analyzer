#this model takes in json data from a parameterized transcript and does analysis on the parameters
from collections import defaultdict
import torch
import numpy as np

#deals with tensor filtering
def maskFilter(tensor, matchThreshold=0.45):
    #inputs a tensor and filters according to a threshold, then returns a list of indices
    #where the filter was achieved
    simScores = tensor 
    mask = (simScores > matchThreshold) & (simScores < 0.9)
    filtered = torch.nonzero(mask, as_tuple=True)[0]

    return filtered.tolist()

#proportional distributions across speaker parameters
def compareSpeakers(parameterOutput, parameter):
    #Compute the proportion of air time for each speaker.
    counts = defaultdict(int)
    total = 0

    for entry in parameterOutput:
        speaker = entry['name']
        value = entry[parameter]
        counts[speaker] += value
        total += value

    # Compute proportions
    return {speaker: {f"{parameter}Proportion": (value / total if total > 0 else 0.0)}
            for speaker, value in counts.items()}

#proportional comparisons within individual speaker parameters
def tallySpeakerParam(parameterOutput, parameter, categories):
    # Initialize dictionaries to count 
    counts = defaultdict(lambda: {category: 0 for category in categories + ['total']})

    for entry in parameterOutput:
        speaker = entry['name']
        value = entry[parameter]

        if value in categories:
            counts[speaker][value] += 1
            counts[speaker]['total'] += 1

    # Compute proportions
    proportions = {}
    for speaker, data in counts.items():
        total = data['total']
        proportions[speaker] = {f"{category}Proportion": (data[category] / total if total > 0 else 0.0) for category in categories}

    return proportions

#averages within individual speaker parameters
def avgSpeakerParam(parameterOutput, parameter):
    #Compute the average in a turn
    rateData = defaultdict(list)

    for entry in parameterOutput:
        speaker = entry['name']
        rateData[speaker].append(entry[parameter])

    return {speaker: {f"average{parameter}": sum(rates) / len(rates)} for speaker, rates in rateData.items()}

def avgResponsiveness(prameterOutput):
    rateData = defaultdict(list)

    for entry in prameterOutput:
        speaker = entry['name']
        if entry['responseSimilarity']:
            maxResponseScore = max([i[1] for i in entry['responseSimilarity']])
            rateData[speaker].append(maxResponseScore)

    return {speaker: {f"average responsiveness": sum(rates) / len(rates)} for speaker, rates in rateData.items()}

def avgSelfSimilarity(prameterOutput):
    rateData = defaultdict(list)

    for entry in prameterOutput:
        speaker = entry['name']
        if entry['selfSimilarity']:
            maxSelfRepetitionScore = max([i[1] for i in entry['selfSimilarity']])
            rateData[speaker].append(maxSelfRepetitionScore)

    return {speaker: {f"average self repetition": sum(rates) / len(rates)} for speaker, rates in rateData.items()}

def computeMetrics(parameterOutput):

    airTime = compareSpeakers(parameterOutput, 'airTime')
    wordsSpoken = compareSpeakers(parameterOutput, 'wordLength')
    questions = tallySpeakerParam(parameterOutput, 'qType', ['openEnded', 'closedEnded'])
    narrative = tallySpeakerParam(parameterOutput, 'nType', ['first', 'second', 'third', 'passive'])
    emotions = tallySpeakerParam(parameterOutput, 'emotion', ['positive', 'neutral', 'negative'])
    avgRates = avgSpeakerParam(parameterOutput, 'wpm')
    avgAirTime = avgSpeakerParam(parameterOutput, 'airTime')
    avgRedundancy = avgSpeakerParam(parameterOutput, 'efficiency')
    avgResponse = avgResponsiveness(parameterOutput)
    avgSelfSim = avgSelfSimilarity(parameterOutput)

    speakers = set(airTime.keys())

    # Combine all metrics into a single dictionary
    combined = {}
    for speaker in speakers:
        combined[speaker] = {
            **airTime.get(speaker, {}),
            **wordsSpoken.get(speaker, {}),
            **questions.get(speaker, {}),
            **narrative.get(speaker, {}),
            **emotions.get(speaker, {}),
            **avgRates.get(speaker, {}),
            **avgAirTime.get(speaker, {}),
            **avgRedundancy.get(speaker, {}),
            **avgResponse.get(speaker, {}),
            **avgSelfSim.get(speaker, {}),
        }

    return combined

