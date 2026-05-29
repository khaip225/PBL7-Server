-- Migration 003: Add joined_clients column to training_jobs
-- Purpose: Track which clients have joined a training job
-- Date: 2026-05-16

ALTER TABLE training_jobs
ADD COLUMN IF NOT EXISTS joined_clients JSONB DEFAULT '{}'::jsonb;
