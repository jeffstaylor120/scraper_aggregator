-- User feedback on a run for iteration (emphasize X, include/exclude); used when re-generating.
ALTER TABLE newsletter_runs ADD COLUMN IF NOT EXISTS feedback TEXT;
