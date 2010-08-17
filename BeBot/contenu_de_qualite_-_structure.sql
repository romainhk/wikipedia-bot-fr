-- phpMyAdmin SQL Dump
-- version 3.3.5deb1
-- http://www.phpmyadmin.net
--
-- Serveur: localhost
-- Généré le : Mar 17 Août 2010 à 15:23
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
-- Création: Mar 17 Août 2010 à 14:43
-- Dernière modification: Mar 17 Août 2010 à 14:43
--

CREATE TABLE IF NOT EXISTS `contenu_de_qualite` (
  `langue` varchar(10) COLLATE utf8_bin NOT NULL DEFAULT 'fr' COMMENT 'iso639',
  `page` varchar(255) COLLATE utf8_bin NOT NULL COMMENT 'Nom complet de la page',
  `espacedenom` int(3) unsigned NOT NULL COMMENT '0 ou 100',
  `date` date NOT NULL COMMENT 'de labellisation',
  `label` varchar(40) COLLATE utf8_bin NOT NULL COMMENT 'adq ou ba',
  `taille` int(7) unsigned NOT NULL DEFAULT '0' COMMENT 'en millier de caractères',
  `consultations` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 'du mois précédant',
  PRIMARY KEY (`page`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Liste des articles labelisés';
