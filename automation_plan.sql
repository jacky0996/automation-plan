-- MySQL dump 10.13  Distrib 8.0.33, for macos13 (arm64)
--
-- Host: 127.0.0.1    Database: automation_plan
-- ------------------------------------------------------
-- Server version	8.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts`
--

DROP TABLE IF EXISTS `accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account` varchar(50) NOT NULL,
  `password` varchar(100) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `account_type` varchar(50) NOT NULL DEFAULT 'PTT',
  `status` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `account` (`account`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `activity_log`
--

DROP TABLE IF EXISTS `activity_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `activity_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `action` varchar(100) NOT NULL COMMENT '行為描述',
  `action_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `status` tinyint(1) NOT NULL COMMENT '成功=1,失敗=0',
  `message` text COMMENT '額外訊息',
  `site_name` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `account_id` (`account_id`),
  CONSTRAINT `activity_log_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cmoney_get_board_by_popular`
--

DROP TABLE IF EXISTS `cmoney_get_board_by_popular`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cmoney_get_board_by_popular` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(45) NOT NULL COMMENT '股票代碼',
  `name` varchar(45) NOT NULL COMMENT '股票名稱',
  `last_use_time` date NOT NULL COMMENT '最後使用時間',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=91 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cmoney_push_post`
--

DROP TABLE IF EXISTS `cmoney_push_post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cmoney_push_post` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` int NOT NULL COMMENT '股票代號',
  `content_id` int DEFAULT NULL COMMENT '模板id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `login_logs`
--

DROP TABLE IF EXISTS `login_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `login_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_id` int DEFAULT NULL,
  `login_time` datetime DEFAULT NULL,
  `status` varchar(10) DEFAULT NULL,
  `message` text,
  `login_count` int DEFAULT NULL,
  `site_name` varchar(50) DEFAULT NULL,
  `logout_time` datetime DEFAULT NULL COMMENT '登出時間',
  PRIMARY KEY (`id`),
  KEY `account_id` (`account_id`),
  CONSTRAINT `login_logs_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1171 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `posts`
--

DROP TABLE IF EXISTS `posts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `posts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `board` varchar(50) NOT NULL,
  `title` varchar(255) NOT NULL,
  `content` text,
  `article_id` varchar(100) DEFAULT NULL COMMENT '文章ID',
  `article_url` varchar(255) DEFAULT NULL COMMENT '文章網址',
  `post_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  `platform` varchar(50) NOT NULL DEFAULT 'ptt' COMMENT '發文平台',
  `category` varchar(50) NOT NULL DEFAULT 'test' COMMENT '發文類型',
  `result` enum('success','fail') DEFAULT NULL COMMENT '發文結果',
  `result_message` text COMMENT '結果訊息',
  PRIMARY KEY (`id`),
  KEY `account_id` (`account_id`),
  CONSTRAINT `posts_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ptt_get_post_by_board`
--

DROP TABLE IF EXISTS `ptt_get_post_by_board`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ptt_get_post_by_board` (
  `id` int NOT NULL AUTO_INCREMENT,
  `borad` varchar(45) NOT NULL COMMENT '搜尋看板',
  `limit_replay_count` int NOT NULL DEFAULT '0' COMMENT '推文數需大於此數,才會將找到的文章紀錄',
  `keywords` varchar(45) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `borad_UNIQUE` (`borad`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ptt_push_post`
--

DROP TABLE IF EXISTS `ptt_push_post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ptt_push_post` (
  `id` int NOT NULL AUTO_INCREMENT,
  `board` varchar(225) NOT NULL COMMENT '發文版',
  `aid` varchar(50) NOT NULL COMMENT '文章id',
  `content_id` int NOT NULL COMMENT '推文模板id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `push_tasks`
--

DROP TABLE IF EXISTS `push_tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `push_tasks` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主鍵ID',
  `account_id` int NOT NULL COMMENT '執行推文的帳號ID',
  `post_id` int NOT NULL COMMENT '要推文的文章ID（對應posts表）',
  `board` varchar(50) NOT NULL COMMENT '文章所在的看板名稱',
  `article_id` varchar(100) NOT NULL COMMENT 'PTT系統中的文章ID',
  `push_content` text NOT NULL COMMENT '推文內容',
  `status` enum('pending','completed','failed') NOT NULL DEFAULT 'pending' COMMENT '任務狀態（待處理/完成/失敗）',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '任務建立時間',
  `completed_at` datetime DEFAULT NULL COMMENT '任務完成時間',
  `error_message` text COMMENT '如果失敗，記錄錯誤訊息',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_push_task` (`account_id`,`post_id`) COMMENT '確保同一帳號不會重複推同一篇文章',
  KEY `account_id` (`account_id`) COMMENT '加速查詢特定帳號的推文任務',
  KEY `post_id` (`post_id`) COMMENT '加速查詢特定文章的推文任務',
  CONSTRAINT `push_tasks_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`),
  CONSTRAINT `push_tasks_ibfk_2` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='推文任務管理表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `replay_template`
--

DROP TABLE IF EXISTS `replay_template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `replay_template` (
  `id` int NOT NULL AUTO_INCREMENT,
  `content` varchar(225) NOT NULL COMMENT '內容',
  `site` varchar(45) NOT NULL COMMENT '網站',
  `board` varchar(45) NOT NULL COMMENT '要使用推文的版',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `scheduled_tasks`
--

DROP TABLE IF EXISTS `scheduled_tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `scheduled_tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `task_type` enum('login','post','push') NOT NULL DEFAULT 'login',
  `status` enum('pending','running','completed','failed') DEFAULT 'pending',
  `priority` int DEFAULT '5',
  `next_execution_time` datetime NOT NULL,
  `last_execution_time` datetime DEFAULT NULL,
  `result` enum('success','fail') DEFAULT NULL,
  `result_message` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `account_id` (`account_id`),
  CONSTRAINT `scheduled_tasks_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-04 21:20:35
