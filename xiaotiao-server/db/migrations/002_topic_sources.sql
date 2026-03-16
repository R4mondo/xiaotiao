-- Add sources column to topics table for multi-source tracking
ALTER TABLE topics ADD COLUMN sources TEXT DEFAULT '["arxiv"]';
