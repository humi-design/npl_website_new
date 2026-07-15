-- Nirmal Precision Database Migration
-- Run this script to add all missing columns and tables
-- Note: MySQL 8+ supports ADD COLUMN IF NOT EXISTS. For older versions, some commands may error but can be safely ignored.

-- ============================================
-- PRODUCTS TABLE - Add missing columns
-- ============================================
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `short_description` VARCHAR(500) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `subcategory` VARCHAR(100) DEFAULT NULL;
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
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `canonical_url` VARCHAR(500) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `og_title` VARCHAR(255) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `og_description` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `twitter_title` VARCHAR(255) DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `twitter_description` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `images` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `downloads` TEXT DEFAULT NULL;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `featured` TINYINT(1) DEFAULT 0;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `updated_at` DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `status` VARCHAR(20) DEFAULT 'active';
ALTER TABLE `products` ADD COLUMN IF NOT EXISTS `slug` VARCHAR(255) UNIQUE;

-- ============================================
-- CARTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `carts` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `session_id` varchar(100) DEFAULT NULL,
  `product_id` int DEFAULT NULL,
  `qty` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- COMPARE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `compare` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- CATEGORIES TABLE (Simple)
-- ============================================
CREATE TABLE IF NOT EXISTS `categories` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- QUOTES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `quotes` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(200) DEFAULT NULL,
  `company` varchar(200) DEFAULT NULL,
  `email` varchar(200) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `message` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- CONTACTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `contacts` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(200) DEFAULT NULL,
  `email` varchar(200) DEFAULT NULL,
  `company` varchar(200) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `message` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- COUNTRIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `countries` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL,
  `slug` varchar(100) UNIQUE DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- EXPORT_STATS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `export_stats` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `title` varchar(100) DEFAULT NULL,
  `value` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- QUOTE_ITEMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `quote_items` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `quote_id` int DEFAULT NULL,
  `product_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- PRODUCT_FAQS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `product_faqs` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_id` int DEFAULT NULL,
  `question` varchar(500) DEFAULT NULL,
  `answer` text DEFAULT NULL,
  `order_num` int DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- PRODUCT_RELATED TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `product_related` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_id` int DEFAULT NULL,
  `related_id` int DEFAULT NULL,
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- PRODUCT_CATEGORIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `product_categories` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL,
  `slug` varchar(100) UNIQUE DEFAULT NULL,
  `description` text DEFAULT NULL,
  `parent_id` int DEFAULT NULL,
  `meta_title` varchar(255) DEFAULT NULL,
  `meta_description` text DEFAULT NULL,
  `image` varchar(500) DEFAULT NULL,
  `order_num` int DEFAULT 0,
  `status` varchar(20) DEFAULT 'active',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- MATERIALS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `materials` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL,
  `slug` varchar(100) UNIQUE DEFAULT NULL,
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

-- ============================================
-- INDUSTRIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `industries` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) DEFAULT NULL,
  `slug` varchar(100) UNIQUE DEFAULT NULL,
  `description` text DEFAULT NULL,
  `applications` text DEFAULT NULL,
  `products` text DEFAULT NULL,
  `meta_title` varchar(255) DEFAULT NULL,
  `meta_description` text DEFAULT NULL,
  `image` varchar(500) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'active',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- BLOG_POSTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS `blog_posts` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `title` varchar(255) DEFAULT NULL,
  `slug` varchar(255) UNIQUE DEFAULT NULL,
  `content` text DEFAULT NULL,
  `excerpt` varchar(500) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `tags` varchar(255) DEFAULT NULL,
  `image` varchar(500) DEFAULT NULL,
  `author` varchar(100) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'draft',
  `published_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `meta_title` varchar(255) DEFAULT NULL,
  `meta_description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
