@echo "Train Prune"

for %%a in (
03-30_04-06-05,
03-30_04-15-40,
03-30_04-25-30,
03-30_04-33-04,
03-30_04-41-01,
03-30_04-54-15,
03-30_05-03-41,
03-30_05-11-50,
03-30_05-25-07,
03-30_05-33-23,
03-30_05-45-14,
03-30_05-53-25,
03-30_06-04-45,
03-30_06-16-39,
03-30_06-28-32,
03-30_06-39-57,
03-30_06-51-17,
03-30_07-01-49,
03-30_07-13-33,
03-30_07-24-50,
03-30_07-37-09,
03-30_07-45-25,
03-30_07-56-48,
03-30_08-09-54,
03-30_08-22-38,
03-30_08-35-23,
03-30_08-49-19,
03-30_09-01-51,
03-30_09-11-23,
03-30_09-21-31,
03-30_09-33-18,
03-30_09-46-03,
03-30_09-57-49,
03-30_10-10-28) do (
    CALL python run.py visual --visual_type expectation --file_name %%a
)

PAUSE 
