-- Nirmal Precision Database Migration
-- Run this script once to add all missing columns

-- Add missing columns to products table
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `short_description` VARCHAR(500) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `long_description` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `applications` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `industries` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `materials` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `surface_finish` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `available_sizes` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `thread_types` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `manufacturing_process` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `tolerance` VARCHAR(100) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `quality_standards` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `technical_specifications` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `subcategory` VARCHAR(100) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `canonical_url` VARCHAR(500) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `og_title` VARCHAR(255) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `og_description` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `twitter_title` VARCHAR(255) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `twitter_description` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `images` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `downloads` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `featured` TINYINT(1) DEFAULT 0;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `updated_at` DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP;

-- Create carts table
CREATE TABLE IF NOT EXISTS `carts` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `session_id` varchar(100) DEFAULT NULL,
  `product_id` int DEFAULT NULL,
  `qty` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create compare table
CREATE TABLE IF NOT EXISTS `compare` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `session_id` varchar(100) DEFAULT NULL,
  `product_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create categories table
CREATE TABLE IF NOT EXISTS `categories` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create quotes table
CREATE TABLE IF NOT EXISTS `quotes` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(200) DEFAULT NULL,
  `company` varchar(200) DEFAULT NULL,
  `email` varchar(200) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `message` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create contacts table
CREATE TABLE IF NOT EXISTS `contacts` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(200) DEFAULT NULL,
  `email` varchar(200) DEFAULT NULL,
  `subject` varchar(500) DEFAULT NULL,
  `message` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create countries table
CREATE TABLE IF NOT EXISTS `countries` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL,
  `code` varchar(10) DEFAULT NULL,
  `phone_code` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create export_stats table
CREATE TABLE IF NOT EXISTS `export_stats` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `country` varchar(100) DEFAULT NULL,
  `percentage` float DEFAULT NULL,
  `products` varchar(500) DEFAULT NULL,
  `order_num` int DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create quote_items table
CREATE TABLE IF NOT EXISTS `quote_items` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `quote_session` varchar(100) DEFAULT NULL,
  `product_id` int DEFAULT NULL,
  `qty` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create product_faqs table
CREATE TABLE IF NOT EXISTS `product_faqs` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_id` int DEFAULT NULL,
  `question` varchar(500) DEFAULT NULL,
  `answer` text DEFAULT NULL,
  `order_num` int DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create product_related table
CREATE TABLE IF NOT EXISTS `product_related` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_id` int DEFAULT NULL,
  `related_product_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create product_categories table
CREATE TABLE IF NOT EXISTS `product_categories` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL,
  `slug` varchar(100) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `parent_id` int DEFAULT NULL,
  `meta_title` varchar(255) DEFAULT NULL,
  `meta_description` text DEFAULT NULL,
  `image` varchar(500) DEFAULT NULL,
  `order_num` int DEFAULT 0,
  `status` varchar(20) DEFAULT 'active',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create materials table
CREATE TABLE IF NOT EXISTS `materials` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL,
  `slug` varchar(100) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `properties` text DEFAULT NULL,
  `applications` text DEFAULT NULL,
  `advantages` text DEFAULT NULL,
  `industries` text DEFAULT NULL,
  `meta_title` varchar(255) DEFAULT NULL,
  `meta_description` text DEFAULT NULL,
  `image` varchar(500) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'active',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create industries table
CREATE TABLE IF NOT EXISTS `industries` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL,
  `slug` varchar(100) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `applications` text DEFAULT NULL,
  `products` varchar(500) DEFAULT NULL,
  `meta_title` varchar(255) DEFAULT NULL,
  `meta_description` text DEFAULT NULL,
  `image` varchar(500) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'active',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create blog_posts table
CREATE TABLE IF NOT EXISTS `blog_posts` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `title` varchar(255) DEFAULT NULL,
  `slug` varchar(255) DEFAULT NULL,
  `content` text DEFAULT NULL,
  `excerpt` text DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `tags` text DEFAULT NULL,
  `author` varchar(100) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'draft',
  `published_at` datetime DEFAULT NULL,
  `meta_title` varchar(255) DEFAULT NULL,
  `meta_description` text DEFAULT NULL,
  `image` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
