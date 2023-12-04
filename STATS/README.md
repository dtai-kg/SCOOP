# SCOOP Evaluation

This folder constains extracted shapes from different systems and the evaluation results.
The shapes produced by SCOOP starts with "SCOOP", and those produced by RML2SHACL, Astrea, and XSD2SHACL are saved in "temp" folder starting with the source name. 

The Qualitative Analysis results can be found in log_target.txt, and the RDF validation results can be found in validation/validation.txt.

## Experiments

We conducted the experiments as showed in the paper.

## Qualitative Analysis 

run stats_target.py to get the results, which are saved in log_target.txt:

```
$ python STATS/stats_target.py
```

## RDF Validation Analysis 

run validation.py to get the validation reports

```
$ python STATS/validation.py 
```

and then run validation_analysis.py to get the validation analysis results, which are saved in validation/validation.txt:
```
$ python STATS/validation_analysis.py 
```