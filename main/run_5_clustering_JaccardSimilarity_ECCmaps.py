import numpy as np
import os.path as osp
import scipy
import matplotlib.pyplot as plt
import seaborn as sns
import sys

sys.path.append('..')

from numpy.random import seed
from sklearn.metrics import jaccard_score
from functions.def_ROIs_EarlyVisualAreas import roi as ROI
from functions.def_ROIs_DorsalEarlyVisualCortex import roi
from sklearn.cluster import SpectralClustering
from functions.individual_variability import grab_data
from scipy.spatial import distance

### Jaccard similarity matrix ###
# All individuals
with open('./../list_subj') as fp:
    subjects = fp.read().split("\n")
list = subjects[0:len(subjects) - 1]

# Mask - Early visual cortex
final_mask_L_ROI, final_mask_R_ROI, index_L_mask_ROI, index_R_mask_ROI = \
    ROI(['ROI'])

# Mask - Dorsal early visual cortex
final_mask_L, final_mask_R, index_L_mask, index_R_mask = \
    roi(['ROI'])

# Mask for eccentricity range
eccentricity_mask_LH = np.reshape(
    np.load('./MaskEccentricity_'
            'above1below8ecc_LH.npz')['list'], (-1))

# Final mask
mask_LH = final_mask_L_ROI + final_mask_L
mask_LH[mask_LH != 2] = 0
mask_LH[mask_LH == 2] = 1
mask_LH = mask_LH[final_mask_L_ROI == 1] * eccentricity_mask_LH

# Import polar angle maps and concatenate maps
dataset_segmented = []
dataset_orig = []
for i in list:
    data = grab_data('eccentricity', i, final_mask_L_ROI, 'LH')
    dataset_orig.append(data[final_mask_L[final_mask_L_ROI == 1] == 1])

    # Binarizing
    data[(data >= 0) & (data <= 2)] = 0
    data[(data > 2) & (data <= 4)] = 2
    data[(data > 4) & (data <= 6)] = 4
    data[(data > 6)] = 6

    data = data[mask_LH == 1]
    dataset_segmented.append(data)

# Jaccard similarity
jaccard_matrix = np.zeros((181, 181))
for i in range(181):
    for j in range(181):
        jaccard_1 = jaccard_score(dataset_segmented[i],
                                  dataset_segmented[j],
                                  average='weighted')
        jaccard_2 = jaccard_score(dataset_segmented[j],
                                  dataset_segmented[i],
                                  average='weighted')
        jaccard_matrix[i, j] = (jaccard_1 + jaccard_2) / 2

# Plot jaccard matrix
sns.heatmap(jaccard_matrix, cmap="flare_r")
plt.show()


#### Clustering ####
# Spectral clustering
n_cluster = 6
clustering = SpectralClustering(n_clusters=n_cluster,
                                random_state=123,
                                affinity='precomputed').fit_predict(
    jaccard_matrix)
np.savez('./../output/clusters_individualIndeces_ecc.npz', list=clustering)

# Cluster means
dataset_orig = np.reshape(dataset_orig, np.shape(dataset_orig)[:-1])
for i in range(n_cluster):
    np.savez('./../output/cluster_' + str(i) + '_eccMaps_weightedJaccard_eccentricityMask.npz',
             list=np.mean(dataset_orig[np.where(clustering == i)], axis=0))

# Reordering
ordering = np.array([])
for i in range(n_cluster):
    ordering = np.concatenate((ordering, np.where(clustering == i)[0]), axis=0)
ordering = ordering.astype(int)

cluster_matrix = np.ones((181, 181))
for i in range(n_cluster):
    indeces = np.where(clustering == i)[0]
    for j in indeces:
        for k in indeces:
            cluster_matrix[j][k] = cluster_matrix[j][k] * (i + 2)

# # Average within cluster
# off_diagonal_triu = np.triu(cluster_matrix, k=1)
# mean_within = np.mean(jaccard_matrix[off_diagonal_triu > 1])
# sd_within = np.std(jaccard_matrix[off_diagonal_triu > 1])

# # Average between cluster
# mean_between = np.mean(jaccard_matrix[off_diagonal_triu == 1])
# sd_between = np.std(jaccard_matrix[off_diagonal_triu == 1])

# Plot of ordered jaccard matrix
sns.heatmap(jaccard_matrix[ordering].T[ordering].T, cmap="flare_r")
plt.show()
