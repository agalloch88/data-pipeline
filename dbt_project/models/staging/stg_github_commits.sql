-- source: main.raw_github_commits
select
  sha as sha,
  repo as repo,
  message as message,
  author_name as author_name,
  author_email as author_email,
  try_cast(timestamp as timestamp) as committed_at,
  url as url
from main.raw_github_commits
