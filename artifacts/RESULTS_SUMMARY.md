# Experiment Results Summary

## Experiment

- 50,000 unique RockYou examples sampled across the archive
- 50,000 generated strong random examples
- 64,000 training, 16,000 calibration, and 20,000 test examples
- Fixed random seed: 42
- Character n-grams (2-4) plus numeric and pattern features
- The same test set was used for both learned models and the LUDS baseline

## Initial results

| Model | Accuracy | Precision | Recall | F1 | Complex-looking leaked recall | Mean inference time |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 99.77% | 99.90% | 99.64% | 99.77% | 94.83% | 0.030 ms |
| Random Forest | 99.79% | 99.76% | 99.81% | 99.79% | 97.13% | 0.032 ms |
| LUDS baseline | 97.39% | 100.00% | 94.78% | 97.32% | 0.00% | 0.003 ms |

Logistic Regression was selected because its F1 score was within one percentage
point of Random Forest while its serialized model was approximately 48.5 KB,
compared with approximately 6.39 MB for Random Forest. This supports the Part A
goal of balancing performance, simplicity, and portability.

## Interpretation

The learned models exceeded the 85% target described in Part A and both detected
far more of the 522 composition-rule-compliant leaked examples than LUDS. The
very high scores must be interpreted cautiously: the negative class consists of
generated strong strings, so the experiment is easier than distinguishing all
real-world secure and insecure user choices. These results validate the
prototype on its defined experimental distribution; they do not establish a
literal probability of future leakage or universal real-world accuracy.
