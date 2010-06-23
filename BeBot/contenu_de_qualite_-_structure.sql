-- phpMyAdmin SQL Dump
-- version 3.3.3deb1
-- http://www.phpmyadmin.net
--
-- Serveur: localhost
-- Généré le : Mer 23 Juin 2010 à 12:25
-- Version du serveur: 5.1.47
-- Version de PHP: 5.3.2-1

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
-- Création: Mer 23 Juin 2010 à 12:17
-- Dernière modification: Mer 23 Juin 2010 à 12:23
--

CREATE TABLE IF NOT EXISTS `contenu_de_qualite` (
  `page` varchar(255) COLLATE utf8_bin NOT NULL COMMENT 'Nom complet de la page',
  `espacedenom` int(3) unsigned NOT NULL COMMENT '0 ou 100',
  `date` date NOT NULL COMMENT 'de labellisation',
  `label` varchar(40) COLLATE utf8_bin NOT NULL COMMENT 'adq ou ba',
  PRIMARY KEY (`page`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Liste des articles labelisés';
