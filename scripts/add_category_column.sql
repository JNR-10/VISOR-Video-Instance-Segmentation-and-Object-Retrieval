-- Add category column to segmented_objects table
ALTER TABLE segmented_objects ADD COLUMN IF NOT EXISTS category VARCHAR;
