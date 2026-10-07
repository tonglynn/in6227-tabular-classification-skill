# Reflection - IN6227 Assignment 1, Variant 2

## Human oversight

I treated the generated files as drafts and checked the intermediate outputs before accepting the final report. I first reviewed `profile.json` and `preprocess_config.json` to make sure the target was `label`, that the missing values had been identified, and that the numeric and categorical columns were assigned sensible preprocessing. I then checked `results.json` and `run_manifest.json` after training. In particular, I checked that preprocessing was inside the sklearn pipeline, that cross-validation was stratified, and that the test set was used only after model selection.

I also reviewed the report layout against the supplied Word template. The report contains the required sections, the first two pages are the generated report, and the Reflection follows after those pages. Before accepting the result, I opened the final PDF and manually checked the VITA block. The GitHub URL shown there was the repository I intended to submit:
`https://github.com/tonglynn/in6227-tabular-classification-skill`.

I accepted the result because the report numbers matched the structured outputs, the report stayed within the two-page limit, and the final PDF contained my name, matric number, model metadata, LLM interface, and repository link. If I ran the workflow again, I would spend more time tuning the models inside cross-validation and would include a clearer comparison of different classification thresholds.

## Critical evaluation

The decision I questioned most was using mean cross-validation F1 as the main model-selection metric. It is a reasonable default because the classes are imbalanced and F1 considers both precision and recall, but it does not reflect every possible cost of an error.

For this dataset, RandomForest had the best CV F1 at 0.6641, while LogisticRegression was very close at 0.6602. LogisticRegression had much higher recall for the minority class (0.849 versus 0.715), although its precision was lower. If missing a positive case were more serious than raising a false alarm, I would choose LogisticRegression or tune the decision threshold instead of automatically accepting RandomForest. I therefore agree with F1 as a transparent default for this assignment, but I would not treat it as the only acceptable decision rule in a real application.

I also chose not to add SMOTE or extensive feature engineering. That kept the workflow easier to explain and avoided introducing another possible source of leakage. The trade-off is that the models use mostly sensible defaults rather than a carefully tuned search, so the result should be read as a reproducible baseline rather than a production solution.

## Trustworthiness

I checked the outputs in more than one place instead of relying only on the narrative report. The class counts in `profile.json` are 23,645 `no` and 7,464 `yes`, which sum to 31,109 after the three rows with missing targets are removed. The confusion matrix in `results.json` is `[[8762, 1403], [901, 2267]]`; its entries sum to 13,333, the reported test-set size.

I manually opened the final PDF and checked the GitHub URL in the VITA section. I also compared the displayed RandomForest F1 values with `results.json`: the report shows CV F1 `0.6641` and test F1 `0.6631`, which match the underlying values when rounded to four decimal places. These checks gave me confidence that the report was generated from the actual run rather than being filled in manually.
