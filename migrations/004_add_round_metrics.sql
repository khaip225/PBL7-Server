-- Migration 004: Add advanced metrics columns to rounds table
-- Purpose: Store per-round AUROC, AUPRC, F1, precision, recall, per-class breakdowns, prototype data
-- Date: 2026-05-29

ALTER TABLE rounds
ADD COLUMN IF NOT EXISTS auroc_macro DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS auprc_macro DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS f1_macro DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS precision_macro DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS recall_macro DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS per_class_auroc JSONB,
ADD COLUMN IF NOT EXISTS per_class_auprc JSONB,
ADD COLUMN IF NOT EXISTS prototype_data JSONB;
