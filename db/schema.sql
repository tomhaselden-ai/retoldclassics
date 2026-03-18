CREATE DATABASE  IF NOT EXISTS `persistent_story_universe` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `persistent_story_universe`;
-- MySQL dump 10.13  Distrib 8.0.38, for Win64 (x86_64)
--
-- Host: localhost    Database: persistent_story_universe
-- ------------------------------------------------------
-- Server version	8.0.38

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
  `account_id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `subscription_level` varchar(50) DEFAULT 'free',
  `story_security` varchar(50) DEFAULT 'private',
  `allowed_classics_authors` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts`
--

LOCK TABLES `accounts` WRITE;
/*!40000 ALTER TABLE `accounts` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bookshelves`
--

DROP TABLE IF EXISTS `bookshelves`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bookshelves` (
  `bookshelf_id` int NOT NULL AUTO_INCREMENT,
  `reader_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`bookshelf_id`),
  KEY `reader_id` (`reader_id`),
  CONSTRAINT `bookshelves_ibfk_1` FOREIGN KEY (`reader_id`) REFERENCES `readers` (`reader_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bookshelves`
--

LOCK TABLES `bookshelves` WRITE;
/*!40000 ALTER TABLE `bookshelves` DISABLE KEYS */;
/*!40000 ALTER TABLE `bookshelves` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `character_relationships`
--

DROP TABLE IF EXISTS `character_relationships`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `character_relationships` (
  `relationship_id` int NOT NULL AUTO_INCREMENT,
  `character_a` int DEFAULT NULL,
  `character_b` int DEFAULT NULL,
  `relationship_type` varchar(100) DEFAULT NULL,
  `relationship_strength` int DEFAULT '50',
  `last_interaction` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`relationship_id`),
  KEY `character_a` (`character_a`),
  KEY `character_b` (`character_b`),
  CONSTRAINT `character_relationships_ibfk_1` FOREIGN KEY (`character_a`) REFERENCES `characters` (`character_id`),
  CONSTRAINT `character_relationships_ibfk_2` FOREIGN KEY (`character_b`) REFERENCES `characters` (`character_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `character_relationships`
--

LOCK TABLES `character_relationships` WRITE;
/*!40000 ALTER TABLE `character_relationships` DISABLE KEYS */;
/*!40000 ALTER TABLE `character_relationships` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `character_visual_profiles`
--

DROP TABLE IF EXISTS `character_visual_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `character_visual_profiles` (
  `visual_profile_id` int NOT NULL AUTO_INCREMENT,
  `character_id` int DEFAULT NULL,
  `reference_images` json DEFAULT NULL,
  `visual_embedding` text,
  `style_rules` json DEFAULT NULL,
  PRIMARY KEY (`visual_profile_id`),
  KEY `character_id` (`character_id`),
  CONSTRAINT `character_visual_profiles_ibfk_1` FOREIGN KEY (`character_id`) REFERENCES `characters` (`character_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `character_visual_profiles`
--

LOCK TABLES `character_visual_profiles` WRITE;
/*!40000 ALTER TABLE `character_visual_profiles` DISABLE KEYS */;
/*!40000 ALTER TABLE `character_visual_profiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `characters`
--

DROP TABLE IF EXISTS `characters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `characters` (
  `character_id` int NOT NULL AUTO_INCREMENT,
  `world_id` int DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `species` varchar(100) DEFAULT NULL,
  `personality_traits` json DEFAULT NULL,
  `home_location` int DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`character_id`),
  KEY `world_id` (`world_id`),
  KEY `home_location` (`home_location`),
  CONSTRAINT `characters_ibfk_1` FOREIGN KEY (`world_id`) REFERENCES `worlds` (`world_id`),
  CONSTRAINT `characters_ibfk_2` FOREIGN KEY (`home_location`) REFERENCES `locations` (`location_id`)
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `characters`
--

LOCK TABLES `characters` WRITE;
/*!40000 ALTER TABLE `characters` DISABLE KEYS */;
INSERT INTO `characters` VALUES (1,1,'Rowan','Fox','[\"curious\", \"clever\", \"helpful\"]',3,'2026-03-12 20:15:42'),(2,1,'Pip','Sparrow','[\"cheerful\", \"brave\"]',1,'2026-03-12 20:15:42'),(3,1,'Tarin','Turtle','[\"wise\", \"patient\"]',2,'2026-03-12 20:15:42'),(4,2,'Luma','Dolphin','[\"playful\", \"smart\"]',4,'2026-03-12 20:15:42'),(5,2,'Maris','Octopus','[\"clever\", \"inventive\"]',5,'2026-03-12 20:15:42'),(6,1,'Ari of Enchanted','Fox','[\"curious\", \"brave\"]',7,'2026-03-12 20:30:43'),(7,1,'Luma of Enchanted','Bird','[\"cheerful\", \"quick\"]',7,'2026-03-12 20:30:43'),(8,1,'Tarin of Enchanted','Turtle','[\"wise\", \"patient\"]',7,'2026-03-12 20:30:43'),(9,2,'Ari of Undersea','Fox','[\"curious\", \"brave\"]',10,'2026-03-12 20:30:43'),(10,2,'Luma of Undersea','Bird','[\"cheerful\", \"quick\"]',10,'2026-03-12 20:30:43'),(11,2,'Tarin of Undersea','Turtle','[\"wise\", \"patient\"]',10,'2026-03-12 20:30:43'),(12,3,'Ari of Castle','Fox','[\"curious\", \"brave\"]',13,'2026-03-12 20:30:43'),(13,3,'Luma of Castle','Bird','[\"cheerful\", \"quick\"]',13,'2026-03-12 20:30:43'),(14,3,'Tarin of Castle','Turtle','[\"wise\", \"patient\"]',13,'2026-03-12 20:30:43'),(15,4,'Ari of Space','Fox','[\"curious\", \"brave\"]',16,'2026-03-12 20:30:43'),(16,4,'Luma of Space','Bird','[\"cheerful\", \"quick\"]',16,'2026-03-12 20:30:43'),(17,4,'Tarin of Space','Turtle','[\"wise\", \"patient\"]',16,'2026-03-12 20:30:43'),(18,5,'Ari of Hidden','Fox','[\"curious\", \"brave\"]',19,'2026-03-12 20:30:43'),(19,5,'Luma of Hidden','Bird','[\"cheerful\", \"quick\"]',19,'2026-03-12 20:30:43'),(20,5,'Tarin of Hidden','Turtle','[\"wise\", \"patient\"]',19,'2026-03-12 20:30:43'),(21,6,'Ari of Sky','Fox','[\"curious\", \"brave\"]',22,'2026-03-12 20:30:43'),(22,6,'Luma of Sky','Bird','[\"cheerful\", \"quick\"]',22,'2026-03-12 20:30:43'),(23,6,'Tarin of Sky','Turtle','[\"wise\", \"patient\"]',22,'2026-03-12 20:30:43'),(24,7,'Ari of Crystal','Fox','[\"curious\", \"brave\"]',25,'2026-03-12 20:30:44'),(25,7,'Luma of Crystal','Bird','[\"cheerful\", \"quick\"]',25,'2026-03-12 20:30:44'),(26,7,'Tarin of Crystal','Turtle','[\"wise\", \"patient\"]',25,'2026-03-12 20:30:44'),(27,8,'Ari of Mystic','Fox','[\"curious\", \"brave\"]',28,'2026-03-12 20:30:44'),(28,8,'Luma of Mystic','Bird','[\"cheerful\", \"quick\"]',28,'2026-03-12 20:30:44'),(29,8,'Tarin of Mystic','Turtle','[\"wise\", \"patient\"]',28,'2026-03-12 20:30:44'),(30,9,'Ari of Frozen','Fox','[\"curious\", \"brave\"]',31,'2026-03-12 20:30:44'),(31,9,'Luma of Frozen','Bird','[\"cheerful\", \"quick\"]',31,'2026-03-12 20:30:44'),(32,9,'Tarin of Frozen','Turtle','[\"wise\", \"patient\"]',31,'2026-03-12 20:30:44'),(33,10,'Ari of Golden','Fox','[\"curious\", \"brave\"]',34,'2026-03-12 20:30:44'),(34,10,'Luma of Golden','Bird','[\"cheerful\", \"quick\"]',34,'2026-03-12 20:30:44'),(35,10,'Tarin of Golden','Turtle','[\"wise\", \"patient\"]',34,'2026-03-12 20:30:44'),(36,11,'Ari of Ancient','Fox','[\"curious\", \"brave\"]',37,'2026-03-12 20:30:44'),(37,11,'Luma of Ancient','Bird','[\"cheerful\", \"quick\"]',37,'2026-03-12 20:30:44'),(38,11,'Tarin of Ancient','Turtle','[\"wise\", \"patient\"]',37,'2026-03-12 20:30:44'),(39,12,'Ari of Rainbow','Fox','[\"curious\", \"brave\"]',40,'2026-03-12 20:30:44'),(40,12,'Luma of Rainbow','Bird','[\"cheerful\", \"quick\"]',40,'2026-03-12 20:30:44'),(41,12,'Tarin of Rainbow','Turtle','[\"wise\", \"patient\"]',40,'2026-03-12 20:30:44'),(42,13,'Ari of Clockwork','Fox','[\"curious\", \"brave\"]',43,'2026-03-12 20:30:44'),(43,13,'Luma of Clockwork','Bird','[\"cheerful\", \"quick\"]',43,'2026-03-12 20:30:44'),(44,13,'Tarin of Clockwork','Turtle','[\"wise\", \"patient\"]',43,'2026-03-12 20:30:44'),(45,14,'Ari of Moon','Fox','[\"curious\", \"brave\"]',46,'2026-03-12 20:30:45'),(46,14,'Luma of Moon','Bird','[\"cheerful\", \"quick\"]',46,'2026-03-12 20:30:45'),(47,14,'Tarin of Moon','Turtle','[\"wise\", \"patient\"]',46,'2026-03-12 20:30:45'),(48,15,'Ari of Dream','Fox','[\"curious\", \"brave\"]',49,'2026-03-12 20:30:45'),(49,15,'Luma of Dream','Bird','[\"cheerful\", \"quick\"]',49,'2026-03-12 20:30:45'),(50,15,'Tarin of Dream','Turtle','[\"wise\", \"patient\"]',49,'2026-03-12 20:30:45'),(51,16,'Ari of Hidden','Fox','[\"curious\", \"brave\"]',52,'2026-03-12 20:30:45'),(52,16,'Luma of Hidden','Bird','[\"cheerful\", \"quick\"]',52,'2026-03-12 20:30:45'),(53,16,'Tarin of Hidden','Turtle','[\"wise\", \"patient\"]',52,'2026-03-12 20:30:45'),(54,17,'Ari of Thunder','Fox','[\"curious\", \"brave\"]',55,'2026-03-12 20:30:45'),(55,17,'Luma of Thunder','Bird','[\"cheerful\", \"quick\"]',55,'2026-03-12 20:30:45'),(56,17,'Tarin of Thunder','Turtle','[\"wise\", \"patient\"]',55,'2026-03-12 20:30:45'),(57,18,'Ari of Coral','Fox','[\"curious\", \"brave\"]',58,'2026-03-12 20:30:45'),(58,18,'Luma of Coral','Bird','[\"cheerful\", \"quick\"]',58,'2026-03-12 20:30:45'),(59,18,'Tarin of Coral','Turtle','[\"wise\", \"patient\"]',58,'2026-03-12 20:30:45'),(60,19,'Ari of Fire','Fox','[\"curious\", \"brave\"]',61,'2026-03-12 20:30:45'),(61,19,'Luma of Fire','Bird','[\"cheerful\", \"quick\"]',61,'2026-03-12 20:30:45'),(62,19,'Tarin of Fire','Turtle','[\"wise\", \"patient\"]',61,'2026-03-12 20:30:45'),(63,20,'Ari of Hidden','Fox','[\"curious\", \"brave\"]',64,'2026-03-12 20:30:46'),(64,20,'Luma of Hidden','Bird','[\"cheerful\", \"quick\"]',64,'2026-03-12 20:30:46'),(65,20,'Tarin of Hidden','Turtle','[\"wise\", \"patient\"]',64,'2026-03-12 20:30:46'),(66,21,'Ari of Crystal','Fox','[\"curious\", \"brave\"]',67,'2026-03-12 20:30:46'),(67,21,'Luma of Crystal','Bird','[\"cheerful\", \"quick\"]',67,'2026-03-12 20:30:46'),(68,21,'Tarin of Crystal','Turtle','[\"wise\", \"patient\"]',67,'2026-03-12 20:30:46'),(69,22,'Ari of Windy','Fox','[\"curious\", \"brave\"]',70,'2026-03-12 20:30:46'),(70,22,'Luma of Windy','Bird','[\"cheerful\", \"quick\"]',70,'2026-03-12 20:30:46'),(71,22,'Tarin of Windy','Turtle','[\"wise\", \"patient\"]',70,'2026-03-12 20:30:46'),(72,23,'Ari of Shimmering','Fox','[\"curious\", \"brave\"]',73,'2026-03-12 20:30:46'),(73,23,'Luma of Shimmering','Bird','[\"cheerful\", \"quick\"]',73,'2026-03-12 20:30:46'),(74,23,'Tarin of Shimmering','Turtle','[\"wise\", \"patient\"]',73,'2026-03-12 20:30:46'),(75,24,'Ari of Aurora','Fox','[\"curious\", \"brave\"]',76,'2026-03-12 20:30:46'),(76,24,'Luma of Aurora','Bird','[\"cheerful\", \"quick\"]',76,'2026-03-12 20:30:46'),(77,24,'Tarin of Aurora','Turtle','[\"wise\", \"patient\"]',76,'2026-03-12 20:30:46'),(78,25,'Ari of Whispering','Fox','[\"curious\", \"brave\"]',79,'2026-03-12 20:30:46'),(79,25,'Luma of Whispering','Bird','[\"cheerful\", \"quick\"]',79,'2026-03-12 20:30:46'),(80,25,'Tarin of Whispering','Turtle','[\"wise\", \"patient\"]',79,'2026-03-12 20:30:46'),(81,26,'Ari of Great','Fox','[\"curious\", \"brave\"]',82,'2026-03-12 20:30:46'),(82,26,'Luma of Great','Bird','[\"cheerful\", \"quick\"]',82,'2026-03-12 20:30:46'),(83,26,'Tarin of Great','Turtle','[\"wise\", \"patient\"]',82,'2026-03-12 20:30:46'),(84,27,'Ari of Starlight','Fox','[\"curious\", \"brave\"]',85,'2026-03-12 20:30:46'),(85,27,'Luma of Starlight','Bird','[\"cheerful\", \"quick\"]',85,'2026-03-12 20:30:46'),(86,27,'Tarin of Starlight','Turtle','[\"wise\", \"patient\"]',85,'2026-03-12 20:30:47'),(87,28,'Ari of Luminous','Fox','[\"curious\", \"brave\"]',88,'2026-03-12 20:30:47'),(88,28,'Luma of Luminous','Bird','[\"cheerful\", \"quick\"]',88,'2026-03-12 20:30:47'),(89,28,'Tarin of Luminous','Turtle','[\"wise\", \"patient\"]',88,'2026-03-12 20:30:47'),(90,29,'Ari of River','Fox','[\"curious\", \"brave\"]',91,'2026-03-12 20:30:47'),(91,29,'Luma of River','Bird','[\"cheerful\", \"quick\"]',91,'2026-03-12 20:30:47'),(92,29,'Tarin of River','Turtle','[\"wise\", \"patient\"]',91,'2026-03-12 20:30:47'),(93,30,'Ari of Hidden','Fox','[\"curious\", \"brave\"]',94,'2026-03-12 20:30:47'),(94,30,'Luma of Hidden','Bird','[\"cheerful\", \"quick\"]',94,'2026-03-12 20:30:47'),(95,30,'Tarin of Hidden','Turtle','[\"wise\", \"patient\"]',94,'2026-03-12 20:30:47'),(96,31,'Ari of Storm','Fox','[\"curious\", \"brave\"]',97,'2026-03-12 20:30:47'),(97,31,'Luma of Storm','Bird','[\"cheerful\", \"quick\"]',97,'2026-03-12 20:30:47'),(98,31,'Tarin of Storm','Turtle','[\"wise\", \"patient\"]',97,'2026-03-12 20:30:47'),(99,32,'Ari of Emerald','Fox','[\"curious\", \"brave\"]',100,'2026-03-12 20:30:47'),(100,32,'Luma of Emerald','Bird','[\"cheerful\", \"quick\"]',100,'2026-03-12 20:30:47'),(101,32,'Tarin of Emerald','Turtle','[\"wise\", \"patient\"]',100,'2026-03-12 20:30:47');
/*!40000 ALTER TABLE `characters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `epub_books`
--

DROP TABLE IF EXISTS `epub_books`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `epub_books` (
  `epub_id` int NOT NULL AUTO_INCREMENT,
  `story_id` int DEFAULT NULL,
  `epub_url` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`epub_id`),
  KEY `story_id` (`story_id`),
  CONSTRAINT `epub_books_ibfk_1` FOREIGN KEY (`story_id`) REFERENCES `stories_generated` (`story_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `epub_books`
--

LOCK TABLES `epub_books` WRITE;
/*!40000 ALTER TABLE `epub_books` DISABLE KEYS */;
/*!40000 ALTER TABLE `epub_books` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_results`
--

DROP TABLE IF EXISTS `game_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_results` (
  `game_result_id` int NOT NULL AUTO_INCREMENT,
  `reader_id` int DEFAULT NULL,
  `game_type` varchar(50) DEFAULT NULL,
  `difficulty_level` int DEFAULT NULL,
  `score` int DEFAULT NULL,
  `duration_seconds` int DEFAULT NULL,
  `played_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`game_result_id`),
  KEY `reader_id` (`reader_id`),
  CONSTRAINT `game_results_ibfk_1` FOREIGN KEY (`reader_id`) REFERENCES `readers` (`reader_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_results`
--

LOCK TABLES `game_results` WRITE;
/*!40000 ALTER TABLE `game_results` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_results` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `illustrations`
--

DROP TABLE IF EXISTS `illustrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `illustrations` (
  `illustration_id` int NOT NULL AUTO_INCREMENT,
  `scene_id` int DEFAULT NULL,
  `image_url` text,
  `prompt_used` text,
  `generation_model` varchar(100) DEFAULT NULL,
  `generated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`illustration_id`),
  KEY `scene_id` (`scene_id`),
  CONSTRAINT `illustrations_ibfk_1` FOREIGN KEY (`scene_id`) REFERENCES `story_scenes` (`scene_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `illustrations`
--

LOCK TABLES `illustrations` WRITE;
/*!40000 ALTER TABLE `illustrations` DISABLE KEYS */;
/*!40000 ALTER TABLE `illustrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `media_jobs`
--

DROP TABLE IF EXISTS `media_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `media_jobs` (
  `job_id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `story_id` int NOT NULL,
  `job_type` varchar(50) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'pending',
  `error_message` text,
  `result_payload` json DEFAULT NULL,
  `worker_id` varchar(100) DEFAULT NULL,
  `attempt_count` int NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `started_at` timestamp NULL DEFAULT NULL,
  `completed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`job_id`),
  KEY `idx_media_jobs_status_created` (`status`,`created_at`),
  KEY `idx_media_jobs_story_type_created` (`story_id`,`job_type`,`created_at`),
  KEY `fk_media_jobs_account` (`account_id`),
  CONSTRAINT `fk_media_jobs_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_media_jobs_story` FOREIGN KEY (`story_id`) REFERENCES `stories_generated` (`story_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `media_jobs`
--

LOCK TABLES `media_jobs` WRITE;
/*!40000 ALTER TABLE `media_jobs` DISABLE KEYS */;
/*!40000 ALTER TABLE `media_jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `locations` (
  `location_id` int NOT NULL AUTO_INCREMENT,
  `world_id` int DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `description` text,
  PRIMARY KEY (`location_id`),
  KEY `world_id` (`world_id`),
  CONSTRAINT `locations_ibfk_1` FOREIGN KEY (`world_id`) REFERENCES `worlds` (`world_id`)
) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `locations`
--

LOCK TABLES `locations` WRITE;
/*!40000 ALTER TABLE `locations` DISABLE KEYS */;
INSERT INTO `locations` VALUES (1,1,'Berry Meadow','A sunny meadow full of berry bushes.'),(2,1,'Crystal Lake','A quiet lake with clear magical water.'),(3,1,'Whispering Woods','Tall trees whisper secrets in the wind.'),(4,2,'Coral City','A colorful city made of coral.'),(5,2,'Sunken Garden','Ancient ruins covered in sea plants.'),(6,2,'Deep Blue Trench','A mysterious deep ocean trench.'),(7,1,'Central Plaza of Enchanted','The main gathering place of the world.'),(8,1,'Ancient Ruins of Enchanted','Old ruins filled with forgotten history.'),(9,1,'Hidden Path of Enchanted','A quiet path known only to locals.'),(10,2,'Central Plaza of Undersea','The main gathering place of the world.'),(11,2,'Ancient Ruins of Undersea','Old ruins filled with forgotten history.'),(12,2,'Hidden Path of Undersea','A quiet path known only to locals.'),(13,3,'Central Plaza of Castle','The main gathering place of the world.'),(14,3,'Ancient Ruins of Castle','Old ruins filled with forgotten history.'),(15,3,'Hidden Path of Castle','A quiet path known only to locals.'),(16,4,'Central Plaza of Space','The main gathering place of the world.'),(17,4,'Ancient Ruins of Space','Old ruins filled with forgotten history.'),(18,4,'Hidden Path of Space','A quiet path known only to locals.'),(19,5,'Central Plaza of Hidden','The main gathering place of the world.'),(20,5,'Ancient Ruins of Hidden','Old ruins filled with forgotten history.'),(21,5,'Hidden Path of Hidden','A quiet path known only to locals.'),(22,6,'Central Plaza of Sky','The main gathering place of the world.'),(23,6,'Ancient Ruins of Sky','Old ruins filled with forgotten history.'),(24,6,'Hidden Path of Sky','A quiet path known only to locals.'),(25,7,'Central Plaza of Crystal','The main gathering place of the world.'),(26,7,'Ancient Ruins of Crystal','Old ruins filled with forgotten history.'),(27,7,'Hidden Path of Crystal','A quiet path known only to locals.'),(28,8,'Central Plaza of Mystic','The main gathering place of the world.'),(29,8,'Ancient Ruins of Mystic','Old ruins filled with forgotten history.'),(30,8,'Hidden Path of Mystic','A quiet path known only to locals.'),(31,9,'Central Plaza of Frozen','The main gathering place of the world.'),(32,9,'Ancient Ruins of Frozen','Old ruins filled with forgotten history.'),(33,9,'Hidden Path of Frozen','A quiet path known only to locals.'),(34,10,'Central Plaza of Golden','The main gathering place of the world.'),(35,10,'Ancient Ruins of Golden','Old ruins filled with forgotten history.'),(36,10,'Hidden Path of Golden','A quiet path known only to locals.'),(37,11,'Central Plaza of Ancient','The main gathering place of the world.'),(38,11,'Ancient Ruins of Ancient','Old ruins filled with forgotten history.'),(39,11,'Hidden Path of Ancient','A quiet path known only to locals.'),(40,12,'Central Plaza of Rainbow','The main gathering place of the world.'),(41,12,'Ancient Ruins of Rainbow','Old ruins filled with forgotten history.'),(42,12,'Hidden Path of Rainbow','A quiet path known only to locals.'),(43,13,'Central Plaza of Clockwork','The main gathering place of the world.'),(44,13,'Ancient Ruins of Clockwork','Old ruins filled with forgotten history.'),(45,13,'Hidden Path of Clockwork','A quiet path known only to locals.'),(46,14,'Central Plaza of Moon','The main gathering place of the world.'),(47,14,'Ancient Ruins of Moon','Old ruins filled with forgotten history.'),(48,14,'Hidden Path of Moon','A quiet path known only to locals.'),(49,15,'Central Plaza of Dream','The main gathering place of the world.'),(50,15,'Ancient Ruins of Dream','Old ruins filled with forgotten history.'),(51,15,'Hidden Path of Dream','A quiet path known only to locals.'),(52,16,'Central Plaza of Hidden','The main gathering place of the world.'),(53,16,'Ancient Ruins of Hidden','Old ruins filled with forgotten history.'),(54,16,'Hidden Path of Hidden','A quiet path known only to locals.'),(55,17,'Central Plaza of Thunder','The main gathering place of the world.'),(56,17,'Ancient Ruins of Thunder','Old ruins filled with forgotten history.'),(57,17,'Hidden Path of Thunder','A quiet path known only to locals.'),(58,18,'Central Plaza of Coral','The main gathering place of the world.'),(59,18,'Ancient Ruins of Coral','Old ruins filled with forgotten history.'),(60,18,'Hidden Path of Coral','A quiet path known only to locals.'),(61,19,'Central Plaza of Fire','The main gathering place of the world.'),(62,19,'Ancient Ruins of Fire','Old ruins filled with forgotten history.'),(63,19,'Hidden Path of Fire','A quiet path known only to locals.'),(64,20,'Central Plaza of Hidden','The main gathering place of the world.'),(65,20,'Ancient Ruins of Hidden','Old ruins filled with forgotten history.'),(66,20,'Hidden Path of Hidden','A quiet path known only to locals.'),(67,21,'Central Plaza of Crystal','The main gathering place of the world.'),(68,21,'Ancient Ruins of Crystal','Old ruins filled with forgotten history.'),(69,21,'Hidden Path of Crystal','A quiet path known only to locals.'),(70,22,'Central Plaza of Windy','The main gathering place of the world.'),(71,22,'Ancient Ruins of Windy','Old ruins filled with forgotten history.'),(72,22,'Hidden Path of Windy','A quiet path known only to locals.'),(73,23,'Central Plaza of Shimmering','The main gathering place of the world.'),(74,23,'Ancient Ruins of Shimmering','Old ruins filled with forgotten history.'),(75,23,'Hidden Path of Shimmering','A quiet path known only to locals.'),(76,24,'Central Plaza of Aurora','The main gathering place of the world.'),(77,24,'Ancient Ruins of Aurora','Old ruins filled with forgotten history.'),(78,24,'Hidden Path of Aurora','A quiet path known only to locals.'),(79,25,'Central Plaza of Whispering','The main gathering place of the world.'),(80,25,'Ancient Ruins of Whispering','Old ruins filled with forgotten history.'),(81,25,'Hidden Path of Whispering','A quiet path known only to locals.'),(82,26,'Central Plaza of Great','The main gathering place of the world.'),(83,26,'Ancient Ruins of Great','Old ruins filled with forgotten history.'),(84,26,'Hidden Path of Great','A quiet path known only to locals.'),(85,27,'Central Plaza of Starlight','The main gathering place of the world.'),(86,27,'Ancient Ruins of Starlight','Old ruins filled with forgotten history.'),(87,27,'Hidden Path of Starlight','A quiet path known only to locals.'),(88,28,'Central Plaza of Luminous','The main gathering place of the world.'),(89,28,'Ancient Ruins of Luminous','Old ruins filled with forgotten history.'),(90,28,'Hidden Path of Luminous','A quiet path known only to locals.'),(91,29,'Central Plaza of River','The main gathering place of the world.'),(92,29,'Ancient Ruins of River','Old ruins filled with forgotten history.'),(93,29,'Hidden Path of River','A quiet path known only to locals.'),(94,30,'Central Plaza of Hidden','The main gathering place of the world.'),(95,30,'Ancient Ruins of Hidden','Old ruins filled with forgotten history.'),(96,30,'Hidden Path of Hidden','A quiet path known only to locals.'),(97,31,'Central Plaza of Storm','The main gathering place of the world.'),(98,31,'Ancient Ruins of Storm','Old ruins filled with forgotten history.'),(99,31,'Hidden Path of Storm','A quiet path known only to locals.'),(100,32,'Central Plaza of Emerald','The main gathering place of the world.'),(101,32,'Ancient Ruins of Emerald','Old ruins filled with forgotten history.'),(102,32,'Hidden Path of Emerald','A quiet path known only to locals.');
/*!40000 ALTER TABLE `locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `narration_audio`
--

DROP TABLE IF EXISTS `narration_audio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `narration_audio` (
  `audio_id` int NOT NULL AUTO_INCREMENT,
  `story_id` int DEFAULT NULL,
  `scene_id` int DEFAULT NULL,
  `audio_url` text,
  `speech_marks_json` json DEFAULT NULL,
  `voice` varchar(50) DEFAULT 'Joanna',
  `generated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`audio_id`),
  KEY `idx_narration_story_scene` (`story_id`,`scene_id`),
  KEY `fk_narration_scene` (`scene_id`),
  CONSTRAINT `fk_narration_scene` FOREIGN KEY (`scene_id`) REFERENCES `story_scenes` (`scene_id`),
  CONSTRAINT `narration_audio_ibfk_1` FOREIGN KEY (`story_id`) REFERENCES `stories_generated` (`story_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `narration_audio`
--

LOCK TABLES `narration_audio` WRITE;
/*!40000 ALTER TABLE `narration_audio` DISABLE KEYS */;
/*!40000 ALTER TABLE `narration_audio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reader_progress`
--

DROP TABLE IF EXISTS `reader_progress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reader_progress` (
  `reader_id` int NOT NULL,
  `stories_read` int DEFAULT '0',
  `words_mastered` int DEFAULT '0',
  `reading_speed` float DEFAULT NULL,
  `preferred_themes` json DEFAULT NULL,
  `traits_reinforced` json DEFAULT NULL,
  PRIMARY KEY (`reader_id`),
  CONSTRAINT `reader_progress_ibfk_1` FOREIGN KEY (`reader_id`) REFERENCES `readers` (`reader_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reader_progress`
--

LOCK TABLES `reader_progress` WRITE;
/*!40000 ALTER TABLE `reader_progress` DISABLE KEYS */;
/*!40000 ALTER TABLE `reader_progress` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reader_vocabulary_progress`
--

DROP TABLE IF EXISTS `reader_vocabulary_progress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reader_vocabulary_progress` (
  `reader_id` int NOT NULL,
  `word_id` int NOT NULL,
  `mastery_level` int DEFAULT '0',
  `last_seen` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`reader_id`,`word_id`),
  KEY `word_id` (`word_id`),
  CONSTRAINT `reader_vocabulary_progress_ibfk_1` FOREIGN KEY (`reader_id`) REFERENCES `readers` (`reader_id`) ON DELETE CASCADE,
  CONSTRAINT `reader_vocabulary_progress_ibfk_2` FOREIGN KEY (`word_id`) REFERENCES `vocabulary` (`word_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reader_vocabulary_progress`
--

LOCK TABLES `reader_vocabulary_progress` WRITE;
/*!40000 ALTER TABLE `reader_vocabulary_progress` DISABLE KEYS */;
/*!40000 ALTER TABLE `reader_vocabulary_progress` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reader_worlds`
--

DROP TABLE IF EXISTS `reader_worlds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reader_worlds` (
  `reader_world_id` int NOT NULL AUTO_INCREMENT,
  `reader_id` int DEFAULT NULL,
  `world_id` int DEFAULT NULL,
  `derived_world_id` int DEFAULT NULL,
  `custom_name` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reader_world_id`),
  KEY `reader_id` (`reader_id`),
  KEY `world_id` (`world_id`),
  KEY `idx_reader_worlds_derived_world_id` (`derived_world_id`),
  CONSTRAINT `reader_worlds_ibfk_1` FOREIGN KEY (`reader_id`) REFERENCES `readers` (`reader_id`) ON DELETE CASCADE,
  CONSTRAINT `reader_worlds_ibfk_2` FOREIGN KEY (`world_id`) REFERENCES `worlds` (`world_id`),
  CONSTRAINT `reader_worlds_ibfk_3` FOREIGN KEY (`derived_world_id`) REFERENCES `worlds` (`world_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reader_worlds`
--

LOCK TABLES `reader_worlds` WRITE;
/*!40000 ALTER TABLE `reader_worlds` DISABLE KEYS */;
/*!40000 ALTER TABLE `reader_worlds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `readers`
--

DROP TABLE IF EXISTS `readers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `readers` (
  `reader_id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `age` int DEFAULT NULL,
  `reading_level` varchar(50) DEFAULT NULL,
  `gender_preference` varchar(50) DEFAULT NULL,
  `trait_focus` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reader_id`),
  KEY `account_id` (`account_id`),
  CONSTRAINT `readers_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `readers`
--

LOCK TABLES `readers` WRITE;
/*!40000 ALTER TABLE `readers` DISABLE KEYS */;
/*!40000 ALTER TABLE `readers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `scene_versions`
--

DROP TABLE IF EXISTS `scene_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `scene_versions` (
  `scene_version_id` int NOT NULL AUTO_INCREMENT,
  `scene_id` int NOT NULL,
  `version_number` int NOT NULL,
  `scene_text` text,
  `illustration_url` text,
  `audio_url` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`scene_version_id`),
  UNIQUE KEY `unique_scene_version` (`scene_id`,`version_number`),
  CONSTRAINT `scene_versions_ibfk_1` FOREIGN KEY (`scene_id`) REFERENCES `story_scenes` (`scene_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `scene_versions`
--

LOCK TABLES `scene_versions` WRITE;
/*!40000 ALTER TABLE `scene_versions` DISABLE KEYS */;
/*!40000 ALTER TABLE `scene_versions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stories`
--

DROP TABLE IF EXISTS `stories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stories` (
  `story_id` int NOT NULL AUTO_INCREMENT,
  `source_author` varchar(100) DEFAULT NULL,
  `source_story_id` int DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `age_range` varchar(50) DEFAULT NULL,
  `reading_level` varchar(50) DEFAULT NULL,
  `moral` text,
  `characters` json DEFAULT NULL,
  `locations` json DEFAULT NULL,
  `traits` json DEFAULT NULL,
  `themes` json DEFAULT NULL,
  `scenes` json DEFAULT NULL,
  `beats` json DEFAULT NULL,
  `paragraphs_modern` json DEFAULT NULL,
  `narration` json DEFAULT NULL,
  `illustration_prompts` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`story_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stories`
--

LOCK TABLES `stories` WRITE;
/*!40000 ALTER TABLE `stories` DISABLE KEYS */;
/*!40000 ALTER TABLE `stories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stories_generated`
--

DROP TABLE IF EXISTS `stories_generated`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stories_generated` (
  `story_id` int NOT NULL AUTO_INCREMENT,
  `reader_id` int DEFAULT NULL,
  `reader_world_id` int DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `trait_focus` varchar(100) DEFAULT NULL,
  `current_version` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`story_id`),
  KEY `reader_id` (`reader_id`),
  KEY `reader_world_id` (`reader_world_id`),
  CONSTRAINT `stories_generated_ibfk_1` FOREIGN KEY (`reader_id`) REFERENCES `readers` (`reader_id`) ON DELETE CASCADE,
  CONSTRAINT `stories_generated_ibfk_2` FOREIGN KEY (`reader_world_id`) REFERENCES `reader_worlds` (`reader_world_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stories_generated`
--

LOCK TABLES `stories_generated` WRITE;
/*!40000 ALTER TABLE `stories_generated` DISABLE KEYS */;
/*!40000 ALTER TABLE `stories_generated` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `story_events`
--

DROP TABLE IF EXISTS `story_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `story_events` (
  `event_id` int NOT NULL AUTO_INCREMENT,
  `story_id` int DEFAULT NULL,
  `characters` json DEFAULT NULL,
  `location_id` int DEFAULT NULL,
  `event_summary` text,
  PRIMARY KEY (`event_id`),
  KEY `story_id` (`story_id`),
  KEY `idx_story_events_location` (`location_id`),
  CONSTRAINT `fk_story_events_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`) ON DELETE SET NULL,
  CONSTRAINT `story_events_ibfk_1` FOREIGN KEY (`story_id`) REFERENCES `stories_generated` (`story_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `story_events`
--

LOCK TABLES `story_events` WRITE;
/*!40000 ALTER TABLE `story_events` DISABLE KEYS */;
/*!40000 ALTER TABLE `story_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `story_scenes`
--

DROP TABLE IF EXISTS `story_scenes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `story_scenes` (
  `scene_id` int NOT NULL AUTO_INCREMENT,
  `story_id` int DEFAULT NULL,
  `scene_order` int DEFAULT NULL,
  `scene_text` text,
  `illustration_url` text,
  `audio_url` text,
  PRIMARY KEY (`scene_id`),
  UNIQUE KEY `unique_scene_order` (`story_id`,`scene_order`),
  CONSTRAINT `story_scenes_ibfk_1` FOREIGN KEY (`story_id`) REFERENCES `stories_generated` (`story_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `story_scenes`
--

LOCK TABLES `story_scenes` WRITE;
/*!40000 ALTER TABLE `story_scenes` DISABLE KEYS */;
/*!40000 ALTER TABLE `story_scenes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `story_versions`
--

DROP TABLE IF EXISTS `story_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `story_versions` (
  `story_version_id` int NOT NULL AUTO_INCREMENT,
  `story_id` int NOT NULL,
  `version_number` int NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `trait_focus` varchar(100) DEFAULT NULL,
  `version_notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`story_version_id`),
  UNIQUE KEY `unique_story_version` (`story_id`,`version_number`),
  CONSTRAINT `story_versions_ibfk_1` FOREIGN KEY (`story_id`) REFERENCES `stories_generated` (`story_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `story_versions`
--

LOCK TABLES `story_versions` WRITE;
/*!40000 ALTER TABLE `story_versions` DISABLE KEYS */;
/*!40000 ALTER TABLE `story_versions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vector_memory_index`
--

DROP TABLE IF EXISTS `vector_memory_index`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vector_memory_index` (
  `vector_id` varchar(128) NOT NULL,
  `source_type` varchar(50) DEFAULT NULL,
  `source_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`vector_id`),
  KEY `idx_vector_source` (`source_type`,`source_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vector_memory_index`
--

LOCK TABLES `vector_memory_index` WRITE;
/*!40000 ALTER TABLE `vector_memory_index` DISABLE KEYS */;
/*!40000 ALTER TABLE `vector_memory_index` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vocabulary`
--

DROP TABLE IF EXISTS `vocabulary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vocabulary` (
  `word_id` int NOT NULL AUTO_INCREMENT,
  `story_id` int DEFAULT NULL,
  `word` varchar(100) DEFAULT NULL,
  `difficulty_level` int DEFAULT NULL,
  `definition` text,
  `example_sentence` text,
  PRIMARY KEY (`word_id`),
  KEY `idx_story_word` (`story_id`,`word`),
  CONSTRAINT `vocabulary_ibfk_1` FOREIGN KEY (`story_id`) REFERENCES `stories_generated` (`story_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vocabulary`
--

LOCK TABLES `vocabulary` WRITE;
/*!40000 ALTER TABLE `vocabulary` DISABLE KEYS */;
/*!40000 ALTER TABLE `vocabulary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_sessions`
--

DROP TABLE IF EXISTS `game_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_sessions` (
  `session_id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `reader_id` int NOT NULL,
  `game_type` varchar(50) NOT NULL,
  `source_type` varchar(50) NOT NULL,
  `source_story_id` int DEFAULT NULL,
  `difficulty_level` int NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'ready',
  `item_count` int NOT NULL DEFAULT '0',
  `words_attempted` int NOT NULL DEFAULT '0',
  `words_correct` int NOT NULL DEFAULT '0',
  `words_incorrect` int NOT NULL DEFAULT '0',
  `hints_used` int NOT NULL DEFAULT '0',
  `completion_status` varchar(20) NOT NULL DEFAULT 'in_progress',
  `started_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `ended_at` timestamp NULL DEFAULT NULL,
  `duration_seconds` int DEFAULT NULL,
  `session_payload` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  KEY `idx_game_sessions_reader_started` (`reader_id`,`started_at`),
  KEY `idx_game_sessions_reader_type_started` (`reader_id`,`game_type`,`started_at`),
  KEY `fk_game_sessions_account` (`account_id`),
  KEY `fk_game_sessions_story` (`source_story_id`),
  CONSTRAINT `fk_game_sessions_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_game_sessions_reader` FOREIGN KEY (`reader_id`) REFERENCES `readers` (`reader_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_game_sessions_story` FOREIGN KEY (`source_story_id`) REFERENCES `stories_generated` (`story_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_sessions`
--

LOCK TABLES `game_sessions` WRITE;
/*!40000 ALTER TABLE `game_sessions` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `game_word_attempts`
--

DROP TABLE IF EXISTS `game_word_attempts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_word_attempts` (
  `attempt_id` int NOT NULL AUTO_INCREMENT,
  `session_id` int NOT NULL,
  `word_id` int DEFAULT NULL,
  `word_text` varchar(100) NOT NULL,
  `game_type` varchar(50) NOT NULL,
  `attempt_count` int NOT NULL DEFAULT '1',
  `correct` tinyint(1) NOT NULL DEFAULT '0',
  `time_spent_seconds` int NOT NULL DEFAULT '0',
  `hint_used` tinyint(1) NOT NULL DEFAULT '0',
  `skipped` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`attempt_id`),
  KEY `idx_game_word_attempts_session` (`session_id`),
  KEY `idx_game_word_attempts_word` (`word_id`,`game_type`),
  CONSTRAINT `fk_game_word_attempts_session` FOREIGN KEY (`session_id`) REFERENCES `game_sessions` (`session_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_game_word_attempts_word` FOREIGN KEY (`word_id`) REFERENCES `vocabulary` (`word_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_word_attempts`
--

LOCK TABLES `game_word_attempts` WRITE;
/*!40000 ALTER TABLE `game_word_attempts` DISABLE KEYS */;
/*!40000 ALTER TABLE `game_word_attempts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `world_customizations`
--

DROP TABLE IF EXISTS `world_customizations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `world_customizations` (
  `customization_id` int NOT NULL AUTO_INCREMENT,
  `reader_world_id` int DEFAULT NULL,
  `modifications` json DEFAULT NULL,
  PRIMARY KEY (`customization_id`),
  KEY `reader_world_id` (`reader_world_id`),
  CONSTRAINT `world_customizations_ibfk_1` FOREIGN KEY (`reader_world_id`) REFERENCES `reader_worlds` (`reader_world_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `world_customizations`
--

LOCK TABLES `world_customizations` WRITE;
/*!40000 ALTER TABLE `world_customizations` DISABLE KEYS */;
/*!40000 ALTER TABLE `world_customizations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `world_rules`
--

DROP TABLE IF EXISTS `world_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `world_rules` (
  `rule_id` int NOT NULL AUTO_INCREMENT,
  `world_id` int NOT NULL,
  `rule_type` varchar(100) DEFAULT NULL,
  `rule_description` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`rule_id`),
  KEY `world_id` (`world_id`),
  CONSTRAINT `world_rules_ibfk_1` FOREIGN KEY (`world_id`) REFERENCES `worlds` (`world_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `world_rules`
--

LOCK TABLES `world_rules` WRITE;
/*!40000 ALTER TABLE `world_rules` DISABLE KEYS */;
INSERT INTO `world_rules` VALUES (1,1,'animals_can_talk','Animals can speak and reason like humans.','2026-03-12 20:15:42'),(2,1,'magic_exists','Magic occasionally appears in the forest.','2026-03-12 20:15:42'),(3,2,'sea_creatures_talk','Sea creatures communicate freely.','2026-03-12 20:15:42'),(4,2,'magic_currents','Ocean currents may carry magical energy.','2026-03-12 20:15:42'),(5,1,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:43'),(6,2,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:43'),(7,2,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:43'),(8,3,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:43'),(9,3,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:43'),(10,4,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:43'),(11,4,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:43'),(12,5,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:43'),(13,5,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:43'),(14,6,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:43'),(15,6,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:43'),(16,7,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:44'),(17,7,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:44'),(18,8,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:44'),(19,8,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:44'),(20,9,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:44'),(21,9,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:44'),(22,10,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:44'),(23,10,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:44'),(24,11,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:44'),(25,11,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:44'),(26,12,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:44'),(27,12,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:44'),(28,13,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:44'),(29,13,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:44'),(30,14,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:45'),(31,14,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:45'),(32,15,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:45'),(33,15,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:45'),(34,16,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:45'),(35,16,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:45'),(36,17,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:45'),(37,17,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:45'),(38,18,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:45'),(39,18,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:45'),(40,19,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:45'),(41,19,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:45'),(42,20,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:46'),(43,20,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:46'),(44,21,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:46'),(45,21,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:46'),(46,22,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:46'),(47,22,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:46'),(48,23,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:46'),(49,23,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:46'),(50,24,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:46'),(51,24,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:46'),(52,25,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:46'),(53,25,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:46'),(54,26,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:46'),(55,26,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:46'),(56,27,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:46'),(57,27,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:46'),(58,28,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:47'),(59,28,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:47'),(60,29,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:47'),(61,29,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:47'),(62,30,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:47'),(63,30,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:47'),(64,31,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:47'),(65,31,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:47'),(66,32,'magic_exists','Strange magical events occasionally occur.','2026-03-12 20:30:47'),(67,32,'animals_speak','Animals can communicate with others.','2026-03-12 20:30:47');
/*!40000 ALTER TABLE `world_rules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `world_versions`
--

DROP TABLE IF EXISTS `world_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `world_versions` (
  `world_version_id` int NOT NULL AUTO_INCREMENT,
  `world_id` int NOT NULL,
  `version_number` int NOT NULL,
  `world_snapshot` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`world_version_id`),
  UNIQUE KEY `unique_world_version` (`world_id`,`version_number`),
  CONSTRAINT `world_versions_ibfk_1` FOREIGN KEY (`world_id`) REFERENCES `worlds` (`world_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `world_versions`
--

LOCK TABLES `world_versions` WRITE;
/*!40000 ALTER TABLE `world_versions` DISABLE KEYS */;
/*!40000 ALTER TABLE `world_versions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worlds`
--

DROP TABLE IF EXISTS `worlds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `worlds` (
  `world_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `description` text,
  `default_world` tinyint(1) DEFAULT '0',
  `parent_world_id` int DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`world_id`),
  KEY `idx_worlds_parent_world_id` (`parent_world_id`),
  CONSTRAINT `worlds_ibfk_1` FOREIGN KEY (`parent_world_id`) REFERENCES `worlds` (`world_id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `worlds`
--

LOCK TABLES `worlds` WRITE;
/*!40000 ALTER TABLE `worlds` DISABLE KEYS */;
INSERT INTO `worlds` VALUES (1,'Enchanted Forest','A magical forest where animals speak and adventures unfold.',1,'2026-03-12 20:15:42'),(2,'Undersea Kingdom','A vibrant ocean world filled with coral cities and sea creatures.',1,'2026-03-12 20:15:42'),(3,'Castle Realm','A medieval land of castles, knights, and dragons.',0,'2026-03-12 20:20:43'),(4,'Space Explorers','A futuristic universe where young explorers travel between planets.',0,'2026-03-12 20:20:43'),(5,'Hidden Jungle','A dense jungle filled with ancient temples and curious animals.',0,'2026-03-12 20:20:43'),(6,'Sky Kingdom','Floating islands high above the clouds connected by bridges of light.',0,'2026-03-12 20:20:43'),(7,'Crystal Caverns','An underground world of glowing crystals and hidden tunnels.',0,'2026-03-12 20:20:43'),(8,'Mystic Desert','A vast desert with hidden oases and ancient spirits.',0,'2026-03-12 20:22:33'),(9,'Frozen Tundra','A cold northern land of snow creatures and icy caves.',0,'2026-03-12 20:22:33'),(10,'Golden Savannah','Wide grasslands where animals roam beneath golden sunsets.',0,'2026-03-12 20:22:33'),(11,'Ancient Library','A mysterious library containing books that hold magical stories.',0,'2026-03-12 20:22:33'),(12,'Rainbow Valley','A bright valley where colors behave like magic.',0,'2026-03-12 20:22:33'),(13,'Clockwork City','A mechanical city powered by gears and steam.',0,'2026-03-12 20:22:33'),(14,'Moon Colony','A peaceful colony built on the moon.',0,'2026-03-12 20:22:33'),(15,'Dream Meadows','Fields where dreams become real.',0,'2026-03-12 20:22:33'),(16,'Hidden Canyon','Deep canyon passages filled with echoes and secrets.',0,'2026-03-12 20:22:34'),(17,'Thunder Plains','Open plains where storms roll endlessly.',0,'2026-03-12 20:22:34'),(18,'Coral Reef Kingdom','Colorful reefs inhabited by friendly sea creatures.',0,'2026-03-12 20:22:34'),(19,'Fire Mountain','A volcanic world where lava lights the sky.',0,'2026-03-12 20:22:34'),(20,'Hidden Valley','A secret valley protected by towering cliffs.',0,'2026-03-12 20:22:34'),(21,'Crystal Lake Realm','A peaceful realm centered around a glowing lake.',0,'2026-03-12 20:22:34'),(22,'Windy Highlands','Rolling hills where powerful winds shape the land.',0,'2026-03-12 20:22:34'),(23,'Shimmering Coast','Beaches where the ocean sparkles with magic.',0,'2026-03-12 20:22:34'),(24,'Aurora Skies','Floating lands under glowing northern lights.',0,'2026-03-12 20:22:34'),(25,'Whispering Marsh','A misty marsh where reeds whisper ancient stories.',0,'2026-03-12 20:22:34'),(26,'Great Prairie','A wide prairie filled with wild horses.',0,'2026-03-12 20:22:34'),(27,'Starlight Harbor','A harbor where ships sail under star-filled skies.',0,'2026-03-12 20:22:34'),(28,'Luminous Garden','Gardens filled with glowing flowers.',0,'2026-03-12 20:22:34'),(29,'River Kingdom','A kingdom built along a great winding river.',0,'2026-03-12 20:22:34'),(30,'Hidden Isles','Small islands scattered across a peaceful sea.',0,'2026-03-12 20:22:34'),(31,'Storm Peaks','Jagged mountains where lightning strikes often.',0,'2026-03-12 20:22:34'),(32,'Emerald Forest','A lush forest glowing with green light.',0,'2026-03-12 20:22:34');
/*!40000 ALTER TABLE `worlds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `character_canon_profiles`
--

DROP TABLE IF EXISTS `character_canon_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `character_canon_profiles` (
  `canon_id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `character_id` int NOT NULL,
  `world_id` int NOT NULL,
  `reader_world_id` int NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `role_in_world` varchar(255) DEFAULT NULL,
  `species_or_type` varchar(100) DEFAULT NULL,
  `age_category` varchar(100) DEFAULT NULL,
  `gender_presentation` varchar(100) DEFAULT NULL,
  `archetype` varchar(255) DEFAULT NULL,
  `one_sentence_essence` text,
  `full_personality_summary` text,
  `dominant_traits` json DEFAULT NULL,
  `secondary_traits` json DEFAULT NULL,
  `core_motivations` json DEFAULT NULL,
  `fears_and_vulnerabilities` json DEFAULT NULL,
  `moral_tendencies` json DEFAULT NULL,
  `behavioral_rules_usually` json DEFAULT NULL,
  `behavioral_rules_never` json DEFAULT NULL,
  `behavioral_rules_requires_justification` json DEFAULT NULL,
  `speech_style` text,
  `signature_expressions` json DEFAULT NULL,
  `relationship_tendencies` text,
  `growth_arc_pattern` text,
  `continuity_anchors` json DEFAULT NULL,
  `visual_summary` text,
  `form_type` varchar(100) DEFAULT NULL,
  `anthropomorphic_level` varchar(100) DEFAULT NULL,
  `size_and_proportions` text,
  `silhouette_description` text,
  `facial_features` text,
  `eye_description` text,
  `fur_skin_surface_description` text,
  `hair_feather_tail_details` text,
  `clothing_and_accessories` text,
  `signature_physical_features` json DEFAULT NULL,
  `expression_range` text,
  `movement_pose_tendencies` text,
  `color_palette` json DEFAULT NULL,
  `art_style_constraints` text,
  `visual_must_never_change` json DEFAULT NULL,
  `visual_may_change` json DEFAULT NULL,
  `narrative_prompt_pack_short` text,
  `visual_prompt_pack_short` text,
  `continuity_lock_pack` text,
  `source_status` varchar(20) DEFAULT 'legacy',
  `canon_version` int NOT NULL DEFAULT '1',
  `enhanced_at` timestamp NULL DEFAULT NULL,
  `enhanced_by` int DEFAULT NULL,
  `last_reviewed_at` timestamp NULL DEFAULT NULL,
  `is_major_character` tinyint(1) NOT NULL DEFAULT '0',
  `is_locked` tinyint(1) NOT NULL DEFAULT '0',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`canon_id`),
  UNIQUE KEY `uq_character_canon_profiles_scope` (`account_id`,`reader_world_id`,`character_id`),
  KEY `idx_character_canon_profiles_world` (`reader_world_id`,`world_id`),
  CONSTRAINT `fk_character_canon_profiles_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_character_canon_profiles_character` FOREIGN KEY (`character_id`) REFERENCES `characters` (`character_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_character_canon_profiles_reader_world` FOREIGN KEY (`reader_world_id`) REFERENCES `reader_worlds` (`reader_world_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `character_canon_profiles`
--

LOCK TABLES `character_canon_profiles` WRITE;
/*!40000 ALTER TABLE `character_canon_profiles` DISABLE KEYS */;
/*!40000 ALTER TABLE `character_canon_profiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `character_canon_versions`
--

DROP TABLE IF EXISTS `character_canon_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `character_canon_versions` (
  `version_id` int NOT NULL AUTO_INCREMENT,
  `canon_id` int NOT NULL,
  `account_id` int NOT NULL,
  `character_id` int NOT NULL,
  `reader_world_id` int NOT NULL,
  `canon_version` int NOT NULL,
  `source_status` varchar(20) DEFAULT NULL,
  `snapshot_json` json DEFAULT NULL,
  `created_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`version_id`),
  KEY `idx_character_canon_versions_scope` (`account_id`,`reader_world_id`,`character_id`,`canon_version`),
  CONSTRAINT `fk_character_canon_versions_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_character_canon_versions_canon` FOREIGN KEY (`canon_id`) REFERENCES `character_canon_profiles` (`canon_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_character_canon_versions_character` FOREIGN KEY (`character_id`) REFERENCES `characters` (`character_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `character_canon_versions`
--

LOCK TABLES `character_canon_versions` WRITE;
/*!40000 ALTER TABLE `character_canon_versions` DISABLE KEYS */;
/*!40000 ALTER TABLE `character_canon_versions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `character_canon_enhancement_runs`
--

DROP TABLE IF EXISTS `character_canon_enhancement_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `character_canon_enhancement_runs` (
  `enhancement_run_id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `character_id` int NOT NULL,
  `world_id` int NOT NULL,
  `reader_world_id` int NOT NULL,
  `section_mode` varchar(20) NOT NULL,
  `status` varchar(20) NOT NULL,
  `prompt_context_json` json DEFAULT NULL,
  `generated_profile_json` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `applied_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`enhancement_run_id`),
  KEY `idx_character_canon_enhancement_runs_scope` (`account_id`,`reader_world_id`,`character_id`,`enhancement_run_id`),
  CONSTRAINT `fk_character_canon_enhancement_runs_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_character_canon_enhancement_runs_character` FOREIGN KEY (`character_id`) REFERENCES `characters` (`character_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_character_canon_enhancement_runs_reader_world` FOREIGN KEY (`reader_world_id`) REFERENCES `reader_worlds` (`reader_world_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `character_canon_enhancement_runs`
--

LOCK TABLES `character_canon_enhancement_runs` WRITE;
/*!40000 ALTER TABLE `character_canon_enhancement_runs` DISABLE KEYS */;
/*!40000 ALTER TABLE `character_canon_enhancement_runs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blog_posts`
--

DROP TABLE IF EXISTS `blog_posts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blog_posts` (
  `post_id` int NOT NULL AUTO_INCREMENT,
  `slug` varchar(160) NOT NULL,
  `title` varchar(255) NOT NULL,
  `summary` text NOT NULL,
  `body_text` longtext NOT NULL,
  `cover_eyebrow` varchar(120) DEFAULT NULL,
  `author_name` varchar(120) NOT NULL DEFAULT 'Retold Classics Studios',
  `status` varchar(20) NOT NULL DEFAULT 'published',
  `published_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`post_id`),
  UNIQUE KEY `uq_blog_posts_slug` (`slug`),
  KEY `idx_blog_posts_status_published` (`status`,`published_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog_posts`
--

LOCK TABLES `blog_posts` WRITE;
/*!40000 ALTER TABLE `blog_posts` DISABLE KEYS */;
INSERT INTO `blog_posts` (`post_id`, `slug`, `title`, `summary`, `body_text`, `cover_eyebrow`, `author_name`, `status`, `published_at`, `created_at`, `updated_at`) VALUES
(1,'building-gentle-reading-routines-at-home','Building Gentle Reading Routines at Home','Small, repeatable reading moments can do more for confidence than long, high-pressure sessions.','A strong reading routine does not have to feel elaborate. For many families, the best rhythm starts with ten calm minutes, one familiar story, and a predictable place to begin.\n\nYoung readers build confidence when they know what comes next. A steady routine helps them settle in, notice patterns, and connect reading with comfort instead of pressure.\n\nThat is one reason we love a mix of classics, read-aloud support, and playful word practice. Families can revisit trusted stories, notice growth over time, and keep reading connected to everyday life.\n\nStoryBloom is built for that kind of rhythm: a welcoming shelf, child-friendly reading spaces, and family tools that support consistency without making reading time feel like school.','Reading routines','Retold Classics Studios','published',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
(2,'why-classics-still-matter-for-early-readers','Why Classics Still Matter for Early Readers','Timeless stories give children strong language patterns, memorable characters, and stories worth returning to.','Classics endure for a reason. They offer strong story structure, memorable moral questions, and language that invites rereading.\n\nFor early readers, that matters. Familiar tales lower the barrier to entry while still leaving room for curiosity, discussion, and vocabulary growth.\n\nFamilies often tell us that children love revisiting a story once they feel ownership over it. A known tale becomes a place to practice expression, confidence, and comprehension.\n\nThat is the role classics play inside StoryBloom. They are not there as dusty artifacts. They are there as living story touchstones that children can read, hear, and return to as they grow.','Why classics','Retold Classics Studios','published',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
/*!40000 ALTER TABLE `blog_posts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blog_comments`
--

DROP TABLE IF EXISTS `blog_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blog_comments` (
  `comment_id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,
  `author_name` varchar(80) NOT NULL,
  `author_email` varchar(255) NOT NULL,
  `comment_body` text NOT NULL,
  `moderation_status` varchar(20) NOT NULL DEFAULT 'pending',
  `moderation_notes` text,
  `moderated_by_email` varchar(255) DEFAULT NULL,
  `client_ip` varchar(64) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `moderated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`comment_id`),
  KEY `idx_blog_comments_post_status_created` (`post_id`,`moderation_status`,`created_at`),
  CONSTRAINT `fk_blog_comments_post` FOREIGN KEY (`post_id`) REFERENCES `blog_posts` (`post_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog_comments`
--

LOCK TABLES `blog_comments` WRITE;
/*!40000 ALTER TABLE `blog_comments` DISABLE KEYS */;
/*!40000 ALTER TABLE `blog_comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contact_submissions`
--

DROP TABLE IF EXISTS `contact_submissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contact_submissions` (
  `submission_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `email` varchar(255) NOT NULL,
  `subject` varchar(160) NOT NULL,
  `message` text NOT NULL,
  `delivery_status` varchar(20) NOT NULL DEFAULT 'queued',
  `client_ip` varchar(64) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `delivered_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`submission_id`),
  KEY `idx_contact_submissions_status_created` (`delivery_status`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contact_submissions`
--

LOCK TABLES `contact_submissions` WRITE;
/*!40000 ALTER TABLE `contact_submissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `contact_submissions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-12 17:52:26
