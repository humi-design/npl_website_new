-- Nirmal Precision Invoice Generator - schema migration
-- Adds the invoice tables. They are intentionally separate from the existing
-- CRM / product / order tables. Safe to run on an existing database.

-- ============================================
-- INVOICES (header + snapshot of invoice-level data)
-- ============================================
CREATE TABLE IF NOT EXISTS `invoices` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `invoice_number` varchar(100) NOT NULL,
  `revision` int DEFAULT 1,
  `parent_invoice_id` int DEFAULT NULL,
  `revision_of` varchar(100) DEFAULT NULL,
  `is_latest` tinyint(1) DEFAULT 1,
  `invoice_date` date DEFAULT NULL,
  `currency` varchar(10) DEFAULT 'USD',
  `supplier_ac_no` varchar(100) DEFAULT NULL,
  `country_of_origin` varchar(100) DEFAULT NULL,
  `country_of_final_destination` varchar(100) DEFAULT NULL,
  `customer_order_no` varchar(100) DEFAULT NULL,
  `internal_order_no` varchar(100) DEFAULT NULL,
  `hs_code` varchar(100) DEFAULT NULL,
  `claim_duty_drawback` tinyint(1) DEFAULT 0,
  `duty_drawback_statement` text,
  `additional_export_declaration` text,
  `lut_arn_no` varchar(100) DEFAULT NULL,
  `remarks` text,
  `calculated_total` double DEFAULT 0,
  `manual_total_override` tinyint(1) DEFAULT 0,
  `manual_total_value` double DEFAULT NULL,
  `total` double DEFAULT 0,
  `amount_in_words` text,
  `signature_name` varchar(200) DEFAULT NULL,
  `signature_date` date DEFAULT NULL,
  `signature_designation` varchar(200) DEFAULT NULL,
  `signature_image` varchar(500) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'Draft',
  `generated_at` datetime DEFAULT NULL,
  `pdf_path` varchar(500) DEFAULT NULL,
  `source_crm_customer_id` int DEFAULT NULL,
  `source_crm_order_id` int DEFAULT NULL,
  `created_by` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_invoice_number_revision` (`invoice_number`, `revision`),
  KEY `ix_invoices_invoice_number` (`invoice_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- INVOICE ITEMS
-- ============================================
CREATE TABLE IF NOT EXISTS `invoice_items` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `invoice_id` int DEFAULT NULL,
  `item_no` varchar(50) DEFAULT NULL,
  `order_no` varchar(100) DEFAULT NULL,
  `no_of_packages` varchar(50) DEFAULT NULL,
  `package_type` varchar(100) DEFAULT NULL,
  `description` text,
  `quantity` double DEFAULT 0,
  `rate_per_100` double DEFAULT 0,
  `currency` varchar(10) DEFAULT NULL,
  `amount` double DEFAULT 0,
  `manual_amount_override` tinyint(1) DEFAULT 0,
  `hs_code` varchar(100) DEFAULT NULL,
  `duty_drawback_info` text,
  `sort_order` int DEFAULT 0,
  FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- INVOICE EXPORTER DETAILS (snapshot)
-- ============================================
CREATE TABLE IF NOT EXISTS `invoice_exporter_details` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `invoice_id` int DEFAULT NULL,
  `exporter_name` varchar(255) DEFAULT NULL,
  `address_line1` varchar(255) DEFAULT NULL,
  `address_line2` varchar(255) DEFAULT NULL,
  `address_line3` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `pin_code` varchar(50) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `telephone` varchar(100) DEFAULT NULL,
  `email` varchar(200) DEFAULT NULL,
  `gst_number` varchar(100) DEFAULT NULL,
  `iec_number` varchar(100) DEFAULT NULL,
  `supplier_ac_no` varchar(100) DEFAULT NULL,
  FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- INVOICE CONSIGNEE DETAILS (snapshot)
-- ============================================
CREATE TABLE IF NOT EXISTS `invoice_consignee_details` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `invoice_id` int DEFAULT NULL,
  `consignee_name` varchar(255) DEFAULT NULL,
  `company_name` varchar(255) DEFAULT NULL,
  `address_line1` varchar(255) DEFAULT NULL,
  `address_line2` varchar(255) DEFAULT NULL,
  `address_line3` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `postal_code` varchar(50) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `phone` varchar(100) DEFAULT NULL,
  `email` varchar(200) DEFAULT NULL,
  `customer_order_no` varchar(100) DEFAULT NULL,
  `internal_order_no` varchar(100) DEFAULT NULL,
  FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- INVOICE SHIPPING DETAILS (snapshot)
-- ============================================
CREATE TABLE IF NOT EXISTS `invoice_shipping_details` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `invoice_id` int DEFAULT NULL,
  `terms_of_delivery` varchar(255) DEFAULT NULL,
  `payment_terms` varchar(255) DEFAULT NULL,
  `pre_carriage_by` varchar(255) DEFAULT NULL,
  `place_of_receipt` varchar(255) DEFAULT NULL,
  `by_pre_carrier` varchar(255) DEFAULT NULL,
  `port_of_loading` varchar(255) DEFAULT NULL,
  `port_of_discharge` varchar(255) DEFAULT NULL,
  `final_destination` varchar(255) DEFAULT NULL,
  `vessel_flight_no` varchar(255) DEFAULT NULL,
  FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- INVOICE DEFAULTS / COMPANY SETTINGS (editable defaults)
-- ============================================
CREATE TABLE IF NOT EXISTS `invoice_defaults` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `exporter_name` varchar(255) DEFAULT NULL,
  `address_line1` varchar(255) DEFAULT NULL,
  `address_line2` varchar(255) DEFAULT NULL,
  `address_line3` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `pin_code` varchar(50) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `telephone` varchar(100) DEFAULT NULL,
  `email` varchar(200) DEFAULT NULL,
  `gst_number` varchar(100) DEFAULT NULL,
  `iec_number` varchar(100) DEFAULT NULL,
  `supplier_ac_no` varchar(100) DEFAULT NULL,
  `default_currency` varchar(10) DEFAULT 'USD',
  `default_country_of_origin` varchar(100) DEFAULT NULL,
  `default_payment_terms` varchar(255) DEFAULT NULL,
  `default_delivery_terms` varchar(255) DEFAULT NULL,
  `default_lut_arn` varchar(100) DEFAULT NULL,
  `signature_name` varchar(200) DEFAULT NULL,
  `signature_designation` varchar(200) DEFAULT NULL,
  `signature_image` varchar(500) DEFAULT NULL,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_by` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- INVOICE HISTORY (audit trail + issued snapshots)
-- ============================================
CREATE TABLE IF NOT EXISTS `invoice_history` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `invoice_id` int DEFAULT NULL,
  `invoice_number` varchar(100) DEFAULT NULL,
  `revision` int DEFAULT 1,
  `action` varchar(50) DEFAULT NULL,
  `snapshot` longtext,
  `note` varchar(500) DEFAULT NULL,
  `created_by` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  KEY `ix_invoice_history_invoice_id` (`invoice_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- SEED the default company information (editable afterwards in Admin)
-- ============================================
INSERT INTO `invoice_defaults`
  (`exporter_name`, `address_line1`, `address_line2`, `address_line3`,
   `city`, `state`, `pin_code`, `country`, `telephone`, `email`,
   `gst_number`, `default_currency`, `default_country_of_origin`)
SELECT
  'Nirmal Precision Pvt Ltd', '4, Jai Matadi Ind. Estate',
  'Opp. Ekvira Gas Godown', 'B/H Sports Complex',
  'Bhayander-East', 'Maharashtra', '401105', 'INDIA',
  '+91(0) 22 28191035', 'info@nirmalprecision.com',
  '27AACCN3516F2ZP', 'USD', 'INDIA'
WHERE NOT EXISTS (SELECT 1 FROM `invoice_defaults`);
