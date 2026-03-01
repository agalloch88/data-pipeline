-- Fails if a commit timestamp is in the future.
select
  sha,
  repo,
  committed_at
from {{ ref('stg_github_commits') }}
where committed_at is not null
  and committed_at > current_timestamp
