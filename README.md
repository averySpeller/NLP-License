# NLP-License
NLP License Report Generation Tool

This project uses NLP to identify open source licenses found in any ActiveState Python runtime.

## Setup
1. An ActiveState account is required to access the public API
2. You need Python 3.x with the following packages and their dependencies installed: 
* argparse	
* gensim
* nltk
* requests
* scikit-learn
* zipfile2
You can download [nlp-license-workshop](https://platform.activestate.com/AveryS/nlp-license-workshop/distributions) which has all the required dependencies already pre-installed.
2. Clone to repository by clicking the clone button above.
3. Run `python3 license_analysis.py -o AveryS -p nlp-license-workshop` where -o is the platform organization and -p is the paltform project.

## Usage
The script will output both a csv and json file with the final results.

```
name,license_detected,similarity,license_stated,copyright_detected

cpython-3.9.6,['PSF 2'],94.62417089625409,,"Copyright (c) 1991 - 1995, Stichting Mathematisch Centrum Amsterdam,"

Cython-0.29.22,['Apache2.0'],99.96661467755095,Apache,"copyright notice that is included in or attached to the workcopyright license to reproduce, prepare Derivative Works of,"

argparse-1.4.0,['unlicense'],33.79259146749973,Python Software Foundation License,

certifi-2021.5.30,['Apache1.1'],62.604746371507645,MPL-2.0,

chardet-4.0.0,['LGPLv2.1'],99.97834797285817,LGPL,"Copyright (C) 1991, 1999 Free Software Foundation, Inc.copyright law: that is to say, a work containing the Library or acopyright notice for the Library among them, as well as a referencecopyrighted by the Free Software Foundation, write to the FreeCopyright (C) <year>  <name of author>"

charset-normalizer-2.0.4,['MIT'],98.07275931040445,MIT,Copyright (c) 2019 TAHRI Ahmed R.

click-8.0.1,['BSD-3-Clause'],98.77283126115799,BSD-3-Clause,Copyright 2014 Pallets

colorama-0.4.3,['BSD-2-Clause'],75.02401570479074,BSD,Copyright (c) 2010 Jonathan Hartley

flit-3.3.0,['BSD-3-Clause'],98.44258055090904,,"Copyright (c) 2015, Thomas Kluyver and contributors"

flit_core-3.3.0,,0,,
```
## License

Licensed under the Apache 2.0 license. See LICENSE file for details.
