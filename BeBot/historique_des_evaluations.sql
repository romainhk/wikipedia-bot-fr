-- phpMyAdmin SQL Dump
-- version 3.4.1deb1
-- http://www.phpmyadmin.net
--
-- Client: localhost
-- Généré le : Mar 14 Juin 2011 à 16:02
-- Version du serveur: 5.1.49
-- Version de PHP: 5.3.3-7

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Base de données: `u_romainhk_transient`
--

-- --------------------------------------------------------

--
-- Structure de la table `historique_des_evaluations`
--

CREATE TABLE IF NOT EXISTS `historique_des_evaluations` (
  `date` date NOT NULL,
  `maximum` int(10) unsigned NOT NULL,
  `élevée` int(10) unsigned NOT NULL,
  `moyenne` int(10) unsigned NOT NULL,
  `faible` int(10) unsigned NOT NULL,
  `inconnue` int(10) unsigned NOT NULL,
  `total` int(10) unsigned NOT NULL,
  PRIMARY KEY (`date`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Pour graphique_evaluations.py';

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
