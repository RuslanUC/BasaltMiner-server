DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `user_id` bigint not null,
  `login` longtext not null,
  `count` bigint not null,
  `level` bigint not null default 1,
  `gold` double not null default 0,
  `redstone` bigint not null default 0,
  `boost` double not null default 1.0,
  `breakTime` bigint not null default 1500,
  `block` bigint not null default 1,
  `world` bigint not null default 1,
  `duelsTotal` bigint not null default 0,
  `duelsWins` bigint not null default 0,
  `duelsAuto` boolean not null default false,
  `duelsRandom` boolean not null default false,
  `statPoints` bigint not null default 0,
  `stats` longtext not null default "[0, 0, 0]",
  `streamers` longtext not null default "[0, 0, 0, 0]",
  `lastupdate` bigint not null default 0,
  `biba` bigint not null default 0,
  `ban` boolean not null default false,
  `banReason` longtext not null default "?",
  UNIQUE KEY `user_id` (`user_id`) USING HASH
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

DROP TABLE IF EXISTS `duels`;
CREATE TABLE `duels` (
  `user1` bigint not null,
  `user2` bigint not null,
  `winner` bigint not null,
  `completed` boolean not null,
  `time` bigint not null
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;