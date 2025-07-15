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
-- Dumping data for table `accounts`
--

LOCK TABLES `accounts` WRITE;
/*!40000 ALTER TABLE `accounts` DISABLE KEYS */;
INSERT INTO `accounts` VALUES (3,'py134679','ai134679','2025-04-22 22:01:50','PTT',0),(4,'jacky5630','z8063478','2025-05-01 21:36:39','PTT',0),(5,'0928539044','Bkend134679','2025-05-08 21:36:22','CMONEY',1),(6,'lunarshade3','Pf9#zY12x!@','2025-06-04 16:50:27','PTT',1),(7,'catwalkzero','Aq#9kmv73Dew\nAq#9kmv73Dew\nAq#9kmv73Dew','2025-06-04 16:50:27','PTT',0),(8,'iamsolucky','luck2023','2025-06-04 16:50:27','PTT',1);
/*!40000 ALTER TABLE `accounts` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `activity_log`
--

LOCK TABLES `activity_log` WRITE;
/*!40000 ALTER TABLE `activity_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `activity_log` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=1072 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `login_logs`
--

LOCK TABLES `login_logs` WRITE;
/*!40000 ALTER TABLE `login_logs` DISABLE KEYS */;
INSERT INTO `login_logs` VALUES (1016,8,'2025-06-04 16:52:20','成功','下次登入時間: 2025-06-05 18:51:34',1,'PTT','2025-06-04 16:52:30'),(1017,3,'2025-06-04 16:52:20','成功','下次登入時間: 2025-06-05 08:04:58',1,'PTT','2025-06-04 16:52:30'),(1018,4,'2025-06-04 16:52:20','成功','下次登入時間: 2025-06-05 11:38:17',1,'PTT','2025-06-04 16:52:30'),(1019,7,'2025-06-04 16:52:20','成功','下次登入時間: 2025-06-05 22:42:38',1,'PTT','2025-06-04 16:52:30'),(1020,6,'2025-06-04 16:52:20','成功','下次登入時間: 2025-06-05 13:28:26',1,'PTT','2025-06-04 16:52:31'),(1023,5,'2025-06-04 17:25:39','成功','下次登入時間: 2025-06-05 20:23:46',1,'cmoney',NULL),(1024,3,'2025-06-07 15:52:36','成功','下次登入時間: 2025-06-08 12:03:26',1,'PTT','2025-06-07 15:52:47'),(1025,8,'2025-06-07 15:52:36','成功','下次登入時間: 2025-06-08 15:56:38',1,'PTT','2025-06-07 15:52:47'),(1026,4,'2025-06-07 15:52:36','成功','下次登入時間: 2025-06-08 04:02:38',1,'PTT','2025-06-07 15:52:47'),(1027,7,'2025-06-07 15:52:36','成功','下次登入時間: 2025-06-08 19:48:08',1,'PTT','2025-06-07 15:52:47'),(1028,6,'2025-06-07 15:52:37','成功','下次登入時間: 2025-06-08 02:44:12',1,'PTT','2025-06-07 15:52:47'),(1031,5,'2025-06-07 16:08:16','成功','下次登入時間: 2025-06-08 02:50:10',1,'cmoney',NULL),(1032,6,'2025-06-08 08:16:32','成功','下次登入時間: 2025-06-09 09:02:29',1,'PTT','2025-06-08 08:16:42'),(1033,4,'2025-06-08 08:16:32','成功','下次登入時間: 2025-06-09 20:13:26',1,'PTT','2025-06-08 08:16:42'),(1040,5,'2025-06-08 08:52:29','成功','下次登入時間: 2025-06-09 07:53:09',1,'cmoney',NULL),(1041,3,'2025-06-08 22:51:40','成功','下次登入時間: 2025-06-09 12:49:31',1,'PTT','2025-06-08 22:51:51'),(1042,8,'2025-06-08 22:51:40','成功','下次登入時間: 2025-06-09 16:18:09',1,'PTT','2025-06-08 22:51:50'),(1043,7,'2025-06-08 22:51:40','成功','下次登入時間: 2025-06-09 19:10:27',1,'PTT','2025-06-08 22:51:51'),(1044,5,'2025-06-11 05:37:48','失敗','登入失敗，無法確定原因',1,'cmoney',NULL),(1045,6,'2025-06-11 14:29:41','成功','下次登入時間: 2025-06-12 20:44:55',1,'PTT','2025-06-11 14:29:51'),(1046,3,'2025-06-12 18:36:54','成功','下次登入時間: 2025-06-13 10:03:44',1,'PTT','2025-06-12 18:37:04'),(1047,8,'2025-06-13 09:37:33','成功','下次登入時間: 2025-06-14 11:56:37',1,'PTT','2025-06-13 09:37:43'),(1048,7,'2025-06-13 19:52:50','失敗','登入失敗：連線失敗',1,'PTT',NULL),(1049,7,'2025-06-13 19:53:56','失敗','登入失敗：連線失敗',2,'PTT',NULL),(1050,7,'2025-06-13 19:55:03','失敗','登入失敗：連線失敗 | 登入失敗超過3次，帳號已停用',3,'PTT',NULL),(1051,4,'2025-06-13 20:55:49','失敗','登入失敗：連線失敗',1,'PTT',NULL),(1052,4,'2025-06-13 20:56:55','失敗','登入失敗：連線失敗',2,'PTT',NULL),(1053,4,'2025-06-13 20:58:02','失敗','登入失敗：連線失敗 | 登入失敗超過3次，帳號已停用',3,'PTT',NULL),(1054,3,'2025-06-14 15:57:21','失敗','登入失敗：連線失敗',1,'PTT',NULL),(1055,3,'2025-06-14 15:58:28','失敗','登入失敗：連線失敗',2,'PTT',NULL),(1056,3,'2025-06-14 15:59:34','失敗','登入失敗：連線失敗 | 登入失敗超過3次，帳號已停用',3,'PTT',NULL),(1057,8,'2025-06-16 21:16:53','成功','下次登入時間: 2025-06-17 22:20:28',1,'PTT','2025-06-16 21:17:03'),(1058,6,'2025-06-16 21:16:53','成功','下次登入時間: 2025-06-17 06:01:15',1,'PTT','2025-06-16 21:17:04'),(1067,NULL,NULL,NULL,'下次登入時間: 2025-06-17 00:36:55',NULL,NULL,NULL),(1071,5,'2025-06-16 22:29:38','成功','下次登入時間: 2025-06-17 03:24:00',1,'cmoney','2025-06-16 22:29:55');
/*!40000 ALTER TABLE `login_logs` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `posts`
--

LOCK TABLES `posts` WRITE;
/*!40000 ALTER TABLE `posts` DISABLE KEYS */;
INSERT INTO `posts` VALUES (11,5,'6111','大宇資','測試發文',NULL,NULL,'2025-06-16 22:26:30',NULL,'cmoney','test','success',NULL);
/*!40000 ALTER TABLE `posts` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='推文任務管理表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `push_tasks`
--

LOCK TABLES `push_tasks` WRITE;
/*!40000 ALTER TABLE `push_tasks` DISABLE KEYS */;
/*!40000 ALTER TABLE `push_tasks` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-17 22:50:54
