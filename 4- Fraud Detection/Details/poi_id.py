#!/usr/bin/python

import sys
import pickle
sys.path.append("../tools/")

from feature_format import featureFormat, targetFeatureSplit
from tester import dump_classifier_and_data
from sklearn.feature_selection import SelectKBest,f_classif
import matplotlib.pyplot


show_plot = False # switch to show graphs


# use for create an plot graph
def plot_it(features_,data_dict_,title = ''):
    data = featureFormat(data_dict_, features_, sort_keys = False)
    if not show_plot:
        return data
    for point in data:
        matplotlib.pyplot.scatter( point[0], point[1] )
    matplotlib.pyplot.xlabel(features_[0])
    matplotlib.pyplot.ylabel(features_[1])
    matplotlib.pyplot.title(title)
    matplotlib.pyplot.show()
    return data

#custom scorer
def my_custom_loss_func(ground_truth,predictions):
    true_negatives = 0
    false_negatives = 0
    true_positives = 0
    false_positives = 0
    for prediction, truth in zip(predictions, ground_truth):
        if prediction == 0 and truth == 0:
            true_negatives += 1
        elif prediction == 0 and truth == 1:
            false_negatives += 1
        elif prediction == 1 and truth == 0:
            false_positives += 1
        elif prediction == 1 and truth == 1:
            true_positives += 1
        else:
            print "Warning: Found a predicted label not == 0 or 1."
            print "All predictions should take value 0 or 1."
            print "Evaluating performance for processed predictions:"
            break
    try:
        precision = 1.0*true_positives/(true_positives+false_positives)
        recall = 1.0*true_positives/(true_positives+false_negatives)

    except:
        #print "divide by zero :",true_positives,true_negatives,false_positives,false_negatives
        #print predictions
        #print ground_truth
        return 0

    return min(precision,recall)

def printFeatureSelectionPhase():
    # select best features
    selector = SelectKBest(f_classif,k='all')
    selector.fit(features,labels)
    
    # feature selection scores by sorted
    scorearr = []
    for i,v in enumerate(selector.scores_): # index of features and score
        scorearr.append( (features_list[i+1],v))  # find which feature's score is this
    
    scorearr = sorted(scorearr,key=lambda v: v[1] ,reverse = True)

    print "\n\n########## Feature Selection Scores :\n"
    for feature_name,feature_score in scorearr:
        print feature_name.ljust(25) ,'->',feature_score



### Task 1: Select what features you'll use. ########################################################

### features_list is a list of strings, each of which is a feature name.
### The first feature must be "poi".
features_list = ['poi',
                 'deferral_payments',
                 'total_payments',
                 'bonus',
                 'restricted_stock_deferred',
                 'deferred_income',
                 'total_stock_value',
                 'expenses',
                 'exercised_stock_options',
                 'long_term_incentive',
                 'restricted_stock',
                 'shared_receipt_with_poi',
                 'from_this_person_to_poi',
                 'from_poi_to_this_person'
                ]



### Load the dictionary containing the dataset
with open("final_project_dataset.pkl", "r") as data_file:
    data_dict = pickle.load(data_file)




data = featureFormat(data_dict, features_list, sort_keys = False)
labels, features = targetFeatureSplit(data)

print "total data lenght : ",len(data_dict.keys())
print "poi count : ",sum(labels)
print "non-poi count : ",len(labels)- sum(labels)





### Task 2: Remove outliers  ##########################################################

### POI is not continuous , so we cant use regression model and because of size of data, we can inspect it by visual so we can find the outlier

features_list_outlier = ['poi','director_fees'] # I've select director_fees just only see what happend, we can select another value like salary or bonus etc.

data_outlier = plot_it(features_list_outlier,data_dict,'with Outlier')
tmp_arry = []

#to find max value of the data, fill it to an array
for point in data_outlier:
    tmp_arry.append(point[1])

max_val = max(tmp_arry)

remove_key = ""
for k in data_dict:
    if data_dict[k][features_list_outlier[1]] == max_val :
        print "Found Outlier Key :",k
        remove_key = k

#delete it from datadic
data_dict.pop(remove_key,0)
data_dict.pop("THE TRAVEL AGENCY IN THE PARK",0) # from pdf,
data_dict.pop("LOCKHART EUGENE E",0) # from pdf, all vals NAN

# after removing outlier, see data to inspect
plot_it(features_list_outlier,data_dict,'without outlier')




### Task 3: Create new feature(s)   #################################


# we are going to create two new features that show us how many percent person sent an mail to POI's and how many percent took from a POI

for k in data_dict:
    to_messages = data_dict[k]["to_messages"]
    from_messages = data_dict[k]["from_messages"]
    from_this_person_to_poi = data_dict[k]["from_this_person_to_poi"]
    from_poi_to_this_person = data_dict[k]["from_poi_to_this_person"]
    try:
        data_dict[k]["perc_to_poi"] = from_this_person_to_poi / (to_messages*1.0)
    except :
        data_dict[k]["perc_to_poi"] = "NaN"
    try:
        data_dict[k]["perc_from_poi"] = from_poi_to_this_person / (from_messages*1.0)
    except:
        data_dict[k]["perc_from_poi"] = "NaN"

features_list.append('perc_to_poi')
features_list.append('perc_from_poi')

#show_plot = False # dont show at testing ,
plot_it(['poi','perc_to_poi'],data_dict,"graph of new features")

my_dataset = data_dict



### Extract features and labels from dataset for local testing
data = featureFormat(my_dataset, features_list, sort_keys = True)
labels, features = targetFeatureSplit(data)


printFeatureSelectionPhase() # show scores after adding new features ...


### Task 4: Try a varity of classifiers
### Please name your classifier clf for easy export below.
### Note that if you want to do PCA or other multi-stage operations,
### you'll need to use Pipelines. For more info:
### http://scikit-learn.org/stable/modules/pipeline.html

# Provided to give you a starting point. Try a variety of classifiers.
from sklearn.naive_bayes import GaussianNB

from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Imputer ,MinMaxScaler
from sklearn.decomposition import PCA

from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier

from sklearn.metrics import make_scorer,fbeta_score
from time import time



pl = Pipeline([
  ('std', MinMaxScaler()),
  ('selection', SelectKBest()),
  ('pca', PCA()),
  ('clf', SVC())
  ])

###### grid parameters

#Selection parameters
k = [k for k in range(5,len(features_list))]

#pca Parameters
x = [x for x in range(2,5)]

# SVM Parameters

krnls = ["rbf"] #"linear",
c = [100000,10000,1000]
gamma = [0.001,0.01,1,10,100,1000]


param_grid = {
        'selection__k': k,
        'pca__n_components': x,
        'clf__kernel':krnls,     #svm
        'clf__C':c,              #svm
        'clf__gamma':gamma       #svm
            }

score = make_scorer(my_custom_loss_func ,greater_is_better=True)

gs = GridSearchCV(estimator = pl,
                  param_grid = param_grid,
                  scoring = score,
                  cv = StratifiedShuffleSplit( test_size=0.3, random_state=42)
                  )

# train the model
t0 = time()
if 1==0:
    print "Finding best parameters, please wait ... "
    gs.fit(features, labels)
    print "Grid Search time :",round(time()-t0,2),"s"
    print "Best Params :",gs.best_params_

### Task 5: Tune your classifier to achieve better than .3 precision and recall 
### using our testing script. Check the tester.py script in the final project
### folder for details on the evaluation method, especially the test_classifier
### function. Because of the small size of the dataset, the script uses
### stratified shuffle split cross validation. For more info: 
### http://scikit-learn.org/stable/modules/generated/sklearn.cross_validation.StratifiedShuffleSplit.html

from sklearn.cross_validation import train_test_split

features_train, features_test, labels_train, labels_test = \
    train_test_split(features, labels, test_size=0.1, random_state=42)


clf = Pipeline([
                ('scaler', MinMaxScaler()),
                ('selection', SelectKBest(k=9)),
                ('pca', PCA(n_components=4)),
                ('clf', SVC(C=100000,kernel="rbf",gamma=1))
                ])

t0 = time()
clf.fit(features_train,labels_train)
print "Train Time :",round(time()-t0,2),"s"
print "Score Clf : ",clf.score(features_test,labels_test)


# validation ...
#ss = StratifiedShuffleSplit(test_size=0.5, random_state=0)
#for train_index, test_index in ss:
#    ftr_train, ftr_test = features[train_index], features[test_index]
#    lbl_train, lbl_test = labels[train_index], labels[test_index]


### Task 6: Dump your classifier, dataset, and features_list so anyone can
### check your results. You do not need to change anything below, but make sure
### that the version of poi_id.py that you submit can be run on its own and
### generates the necessary .pkl files for validating your results.

dump_classifier_and_data(clf, my_dataset, features_list)
