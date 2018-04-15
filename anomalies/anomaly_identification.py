import pandas as pd
import scipy.stats as ss
import numpy as np
import math
from pandas import to_datetime
from collections import Counter
from sklearn import mixture
import os,gc

def get_percentage(percent, number_of_time_points):
    return int(percent/100*number_of_time_points)

def detect_anomalies(input_directory = "static/anomalies/merged_local_outlier_factor_file.csv", output_directory="static/anomalies/anomalies.csv"):
    anomaly_percentage = 2 #example 2%

    print('anomalies are detecting...')

    data = pd.read_csv(input_directory)
    data.index = data.Index
    data = data.sort_index()

    try:
        data = data[data.lof != 'lof']
    except:
        print()
    new_data = pd.DataFrame()
    new_data['lof'] = data['lof']
    new_data = new_data.astype(float)


    lof = data['lof'].tolist()
    lof = lof[:-1]
    lof = np.array(lof)

    lof = lof.transpose()
    lof = lof.reshape(-1, 1)
    # print(lof)
    # print(len(lof))
    # print(len(data['lof']))
    # print(data['lof'])
    lof = lof.astype(float)
    np.delete(lof, -1)
    lowest_bic = np.infty

    #n_components_range = range(1, 5)
    cv_types = ['spherical', 'tied', 'diag', 'full']

    best_gmm = {}
    for cv_type in cv_types:
        # for n_components in n_components_range:
        # Fit a Gaussian mixture with EM
        gmm = mixture.GaussianMixture(n_components=4,
                                      covariance_type=cv_type)
        gmm.fit(lof)
        bic = gmm.bic(lof)
        if bic < lowest_bic:
            lowest_bic = bic
            best_gmm = gmm

    for i in range(best_gmm.means_.size):
        mu = best_gmm.means_[i]
        variance = best_gmm.covariances_[i]
        sigma = math.sqrt(variance)
        x = np.linspace(mu - 3 * sigma, mu + 3 * sigma, 100)
        y = ss.norm.pdf(x, mu, sigma) * best_gmm.weights_[i]
        #plt.plot(x, y, label='pdf')

    #plt.show()

    # n, bins, patches = plt.hist(X)

    # print('total time points '+ str(len(data)))

    number_of_time_points = len(data)

    amount_of_anomalies = get_percentage(anomaly_percentage, number_of_time_points)

    # sorting by lof descending order
    sorted_data = new_data.sort_values(by=['lof'], ascending=False)

    # get the dates with highest lof values
    anomalies = sorted_data[0:amount_of_anomalies]

    # get abnormal dates
    abnormal_dates = anomalies.index.values.tolist()

    # abnormal_dates = abnormal_dates[1:]
    # abnormal_dates = np.asarray(abnormal_dates)

    abnormal_dates = list(map(lambda x: to_datetime(x).replace(minute=0, second=0, microsecond=0), abnormal_dates))
    print(anomalies)

    anomalies['DateTime'] = anomalies.index.values
    anomalies['DateHour'] = anomalies['DateTime'].apply(lambda x: to_datetime(x).replace(minute=0, second=0, microsecond=0))
    print(anomalies)
    lof_average_per_date = anomalies.groupby('DateHour', as_index=False)['lof'].mean()
    print(lof_average_per_date)
    print(abnormal_dates)

    abnormal_dates_and_counter = Counter(abnormal_dates)
    # print(abnormal_dates_and_counter.keys())  # equals to list(set(words))
    # print(abnormal_dates_and_counter.values())  # counts the elements' frequency

    tmp = pd.DataFrame.from_dict(abnormal_dates_and_counter, orient='index').reset_index()
    count = pd.DataFrame()
    count['DateHour'] = tmp['index']
    count['Count'] = tmp.iloc[:, -1]

    count = count.sort_values(by=['DateHour'])
    count.index = count['DateHour']
    count = count.drop(['DateHour'], axis=1)
    print("length of lof_average_per_date: " + str(len(lof_average_per_date['lof'].values)))
    print("length of count: " + str(len(count['Count'].values)))
    count['Average_lof'] = lof_average_per_date['lof'].values
    count['Ranking_Factor'] = count['Average_lof'] / count['Count']
    count = count.sort_values(by=['Ranking_Factor'])

    number_of_time_points = len(count)

    amount_of_anomalies = get_percentage(anomaly_percentage, number_of_time_points)

    count = count.head(amount_of_anomalies)

    if os.path.exists(output_directory):
        os.remove(output_directory)

    count.to_csv(output_directory)

    with open('static/anomalies/all_anomalies.csv', 'a') as f:
        count.to_csv(f, header=False)

    gc.collect()
    return count


#detect_anomalies(input_directory="D:/coursework/L4S2/GroupProject/repo/TeamFxPortal/static/anomalies/merged_local_outlier_factor_file.csv",
#                 output_directory = "D:/coursework/L4S2/GroupProject/repo/TeamFxPortal/static/anomalies/anomalies.csv")