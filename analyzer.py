#this model takes in json data from a parameterized transcript and does analysis on the parameters
from collections import defaultdict
import torch 

#DEPRECATED

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


# MAIN FUNCTIONS

# calculates the proportion of responses of each person to the other person's statements
def responseCoverage(df):
    # Group statements by 'name' and count unique 'id's for each name
    statement_counts = df.groupby('previous')['id'].nunique()

    # Group responses by 'name' and count unique 'responseID's for each name
    response_counts = df.groupby('name')['responseID'].nunique()

    result = {}

    # Compute proportions of responses to their statements
    for name in statement_counts.index:  # Iterate over unique 'name's
        statement_count = statement_counts.get(name, 0)
        response_count = response_counts.get(name, 0)

        if statement_count == 0:  # Avoid division by zero
            result[name] = 0
        else:
            result[name] = response_count / statement_count  # Use floating-point division

    return result

# Calculating the metrics
def computeMetrics(df):
    avgAirTime = df.groupby(['name', 'turn'])['airTime'].sum().groupby('name').mean()
    avgWPM = df.groupby('name')['wpm'].mean()
    avgResponse = df.groupby('name')['responseScore'].mean()
    avgCoherence = df.groupby('name')['coherenceScore'].mean()
    countQuestions = df.groupby(['name', 'qType'])['qType'].count()
    countNarrative = df.groupby(['name', 'nType'])['nType'].count()
    countEmotion = df.groupby(['name', 'emotion'])['emotion'].count()
    countTopic = df.groupby(['name', 'topic'])['topic'].count()
    propCoverage = responseCoverage(df)
    
    # Initializing the dictionary
    result = {}
    
    # Looping through unique names
    for name in df['name'].unique():
        # Creating nested dictionary for each name
        result[name] = {
            'avgAirTime': avgAirTime.get(name, None),
            'avgWPM': avgWPM.get(name, None),
            'propResponseCover': propCoverage.get(name, None),
            'avgResponseScore': avgResponse.get(name, None),
            'avgCoherenceScore': avgCoherence.get(name, None),
            'countQuestions': countQuestions.loc[name].to_dict() if name in countQuestions else {},
            'countNarrative': countNarrative.loc[name].to_dict() if name in countNarrative else {},
            'countEmotion': countEmotion.loc[name].to_dict() if name in countEmotion else {},
            'countTopic': countTopic.loc[name].to_dict() if name in countTopic else {},
        }
    
    return result

