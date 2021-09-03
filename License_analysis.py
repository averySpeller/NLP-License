# Break down:
# 
# - authenticate
# - get ingredient name and version
# - download file
# - find license file
# - determine which license it is closest to
# - find copyright holder
#

from pathlib import Path
import requests
import subprocess
import os
import json
from io import BytesIO
from zipfile import ZipFile
import tarfile
from urllib.request import urlopen
import sys
import codecs
import shutil
from csv import DictWriter
import csv
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
import gensim
import numpy as np 
import argparse

#simple function to store any line starting with "copyright"
def find_copyright(filename):
    # Using readline()
    copyright = ''
    try:
        file1 = open(filename, 'r')
    except:
        return('')
    while True:
        line = file1.readline()
        # if line is empty
        # end of file is reached
        if not line:
            break
        if line.strip().lower().startswith("copyright"):
            copyright = copyright+ line.strip()
    file1.close()
    return(copyright)

#get licence stated in from PKG_INFO 
def get_license(filename):
    license = ''
    file1 = open(filename, 'r')
    
    while True:
        line = file1.readline()
        # if line is empty
        # end of file is reached
        if not line:
            break
        if line.strip().lower().startswith("license:"):
            try:
                license = line.strip().split(": ")[1]
            except:
                license = ''
    file1.close()
    return(license)

def detect_license(file1):
    max_similarity = 0
    license_similarity = {}
    license_detected = {}
    with os.scandir('reference/') as references:
        for reference in references:
            if not reference.name.startswith("."):
                print("Analyzing: ",reference.name)
                reference_file = "reference/"+reference.name
                #recording docs(sentences) for first file
                file_docs = []
                try:
                    with open (file1) as f:
                        tokens = sent_tokenize(f.read())
                except:
                    license_detected['UNKNOWN'] = 0
                    return(license_detected)

                with open (file1) as f:
                    tokens = sent_tokenize(f.read())
                    for line in tokens:
                        file_docs.append(line)

                print("    Documents in requested license:",len(file_docs))

                #creating word dictionary distinct word to it's id
                gen_docs = [[w.lower() for w in word_tokenize(text)] 
                            for text in file_docs]
                dictionary = gensim.corpora.Dictionary(gen_docs)
                #creating corpus (wordid, count)
                corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
                tf_idf = gensim.models.TfidfModel(corpus)

                try: 
                    sims = gensim.similarities.Similarity('workdir/',tf_idf[corpus], num_features=len(dictionary))
                except Exception as ex:
                    print(ex)
                    sims = 0
                file2_docs = []
                #analyzing reference material
                with open (reference_file) as f:
                    tokens = sent_tokenize(f.read())
                    for line in tokens:
                        file2_docs.append(line)
                print("    Number of documents in {}: {}".format(reference.name,len(file2_docs)))
                avg_sims = [] # array of averages
                max_sims = []
                # for line in query documents
                for line in file2_docs:
                    # tokenize words
                    query_doc = [w.lower() for w in word_tokenize(line)]
                    # create bag of words
                    query_doc_bow = dictionary.doc2bow(query_doc)
                    # find similarity for each document
                    query_doc_tf_idf = tf_idf[query_doc_bow]
                    # print('Comparing Result:', sims[query_doc_tf_idf]) 
                    # calculate sum of similarities for each query doc
                    sum_of_sims =(np.sum(sims[query_doc_tf_idf], dtype=np.float32))
                    #get closest match in docs
                    max_sim = max(sims[query_doc_tf_idf])
                    # print("max: ",max_sim)
                    max_sims.append(max_sim)
                    # calculate average of similarity for each query doc
                    avg = sum_of_sims / len(file_docs)
                    # print average of similarity for each query doc
                    # print(f'avg: {sum_of_sims / len(file_docs)}')
                    # add average values into array
                    avg_sims.append(avg)  
                    # calculate total average
                    total_avg = np.sum(avg_sims, dtype=np.float32)
                    # round the value and multiply by 100 to format it as percentage
                    percentage_of_similarity = round(float(total_avg) * 100)
                    # if percentage is greater than 100
                    # that means documents are almost same
                    if percentage_of_similarity >= 100:
                        percentage_of_similarity = 100

                sum = 0
                for i in max_sims:
                    sum = sum + i
                average = sum/len(max_sims)
                license_similarity[os.path.splitext(reference.name)[0]] = average*100
                print("    Similarity: ", average*100)

    for key, value in license_similarity.items():
        if value > max_similarity:
            license_detected.clear()
            max_similarity = value
            license_detected[key] = value
    print("LICENSE DETECTED: ",license_detected)
    return(license_detected)

parser = argparse.ArgumentParser(
    description='Using NLP to Generate License Report')
parser.add_argument('-o', '--organization',required=True,
                    help='Organization')
parser.add_argument('-p', '--project',required=True,
                    help='Project')                    
args = parser.parse_args()

org = args.organization
project = args.project
jwt = subprocess.run(["state", "export", "jwt"], stdout=subprocess.PIPE, text=True).stdout.rstrip()
url = "https://platform.activestate.com/sv/mediator/api"
query = """{{
    project(org: "{org}", name: "{project}") {{
      __typename
      ... on Project {{
        name
        description
        commit {{
          commit_id
          sources(limit:10){{
            name
            version
            url
          }}
        }}
      }}
      ... on NotFound {{
        message
      }}
    }}
  }}
""".format(org=org, project=project)

json_query  = {"query":query}
headers = {"Authorization": "Bearer %s" % jwt}

r = requests.post(url=url, json=json_query, headers=headers)
sources = r.json()["data"]["project"]["commit"]["sources"]
project = r.json()["data"]["project"]["name"]
print("project: {}/{}".format(org,project))
data = {}
data['package'] = []
check_license_files = ["LICENSE", "LICENSE.txt", "LICENSE.md","LICENSE.rst","COPYING", "COPYING.txt", "COPYING.md","COPYING.rst" ]

count = 0
for s in sources:
    count = count+1
    package_name = s["name"]
    package_version = s["version"]
    name_used = ''
    license_detected = ''
    license_stated = ''
    license_similarity = 0
    copyright_detected = ''
    LICENSE_found = False
    PKG_INFO_found = False
    
    print("\n~~~~~~~~~{}: {} {}~~~~~~~~~~".format(count,package_name,package_version))

# download zip files
    r = requests.get(url=s["url"],headers=headers)
    with open(os.path.basename(s["url"]), "wb") as f:
        f.write(r.content)
    compressed_file_name = f.name
    print(compressed_file_name)

# get file name
    file_name = Path(compressed_file_name).stem
    if ".tar" in file_name:
        file_name = file_name.rsplit('.tar', 1)[0]
    else:
        file_name = file_name
    name_used = file_name 

# Look for LICENSE
    for file in check_license_files:
        try:
            print("Checking: "+file_name+"/"+file)
            tarfile.open(compressed_file_name).extract(file_name+"/"+file)
        except Exception as ex:
            print(ex)
            license_similarity = 0
        else: 
            print("\""+file+"\" found, extracting file!")
            LICENSE_found = True
            #get copyright
            copyright_detected = find_copyright(file_name+"/"+file)
            #detect license
            license_detected = [ key for key in detect_license(file_name+"/"+file)]
            license_similarity = [ detect_license(file_name+"/"+file)[key] for key in detect_license(file_name+"/"+file)][0]
            # print(license_detected, license_similarity)
            break

# look for PKG-INFO
    try:
        tarfile.open(compressed_file_name).extract(file_name+"/PKG-INFO")
    except Exception as ex:
        print(ex)
        try:
            tarfile.open(compressed_file_name).extract(file_name+"/PKG-INFO.txt")
        except Exception as ex:
            print(ex)
        else:
            print("PKG-INFO.txt found, file extracted!")
            PKG_INFO_found = True
            license_stated = get_license(file_name+"/PKG-INFO.txt")
    else:
        print("PKG_INFO found, file extracted!")
        PKG_INFO_found = True
        license_stated = get_license(file_name+"/PKG-INFO")

    if PKG_INFO_found == False and LICENSE_found == False:
        print("UNKNOWN LICENSE")
        try:
            with open("./unknown/"+os.path.basename(s["url"]), "wb") as f:
                f.write(r.content)
        except Exception as ex:
            print(ex)

    data['package'].append({
        'name': name_used,
        'license_detected':license_detected,
        'license_stated':license_stated,
        'license_similarity':license_similarity,
        'copyright_detected':copyright_detected
    })
    ## Removing files created
    shutil.rmtree(file_name)
    os.remove(compressed_file_name)

#write json
with open(project+'_license.json', 'w') as outfile:
    json.dump(data, outfile)

#write CSV
with open(project+'_results.csv', mode='w') as output_file:
    print("Creating Report...")
    fieldnames = ['name','license_detected','similarity','license_stated','copyright_detected']
    writer = csv.DictWriter(output_file, fieldnames=fieldnames)
    writer.writeheader()
    for key, value in data.items():
        for i in value:
            writer.writerow({"name": i["name"], "license_detected": i["license_detected"], "similarity":i["license_similarity"],"license_stated":i["license_stated"],"copyright_detected":i["copyright_detected"]})
    print("Done!")
    print(project+"_results.csv created.")