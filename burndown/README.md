# Make Milestone and Overall Burndown Chart

### Get to repository in your CLI

Make sure you are logged in to your github account on the CLI, and make sure the repository is
cloned on your device.

Use 'cd Rocky' to go to the repo on your device. If the repo is kept within other folders,
you will need to add the full path.

## Milestone Chart

1. Go into milestone_burndown.py and change the date bounds for the chart to match the sprint dates.

2. Paste this code in to the CLI, changing the name to match the milestone name:


(
echo "closedAt,createdAt,number,state,title"
gh issue list --state all --limit 1000 \
  --milestone "Sprint 3 | Setting up demo" \
  --json closedAt,createdAt,number,state,title \
  --jq '.[] | [.closedAt, .createdAt, .number, .state, .title] | @csv'
) > milestone_issues.csv



3. Run milestoneBurndown.py in your CLI like this:


Python3 milestoneBurndown.py

## Overall Chart

1. paste this code in to the CLI:


 (
echo "closedAt,createdAt,number,state,title"
gh issue list --state all --limit 1000 \
  --json closedAt,createdAt,number,state,title \
  --jq '.[] | [.closedAt, .createdAt, .number, .state, .title] | @csv'
) > issues.csv



2. Run it in your CLI like this:


python3 burndown.py







