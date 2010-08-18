-- phpMyAdmin SQL Dump
-- version 3.3.5deb1
-- http://www.phpmyadmin.net
--
-- Serveur: localhost
-- Généré le : Mer 18 Août 2010 à 15:44
-- Version du serveur: 5.1.49
-- Version de PHP: 5.3.2-2

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Base de données: `u_romainhk`
--

-- --------------------------------------------------------

--
-- Structure de la table `contenu_de_qualite`
--

CREATE TABLE IF NOT EXISTS `contenu_de_qualite` (
  `langue` varchar(10) COLLATE utf8_bin NOT NULL DEFAULT 'fr' COMMENT 'iso639',
  `page` varchar(255) COLLATE utf8_bin NOT NULL COMMENT 'Nom complet',
  `espacedenom` int(3) unsigned NOT NULL COMMENT '0 ou 100',
  `date` date NOT NULL COMMENT 'de labellisation',
  `label` varchar(50) COLLATE utf8_bin NOT NULL COMMENT 'adq ou ba',
  `taille` int(7) unsigned NOT NULL DEFAULT '0' COMMENT 'en millier de caractères',
  `consultations` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 'du mois précédant',
  `traduction` varchar(255) COLLATE utf8_bin DEFAULT NULL COMMENT 'Interwiki ou page de suivi',
  `avancement` varchar(15) COLLATE utf8_bin DEFAULT NULL COMMENT 'Cat:Article par avancement',
  `importance` varchar(15) COLLATE utf8_bin DEFAULT NULL COMMENT 'Cat:Article par importance',
  PRIMARY KEY (`page`,`langue`),
  KEY `page` (`page`),
  KEY `langue` (`langue`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Liste des articles labelisés';
