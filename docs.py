index = """
    <h3 style="color: red;">Если вы разработчик официальной версии и вам нужен этот домен - свяжитесь со мной (информация ниже).</h3>
    <h1>Основная информация</h1>
    Это неофициальное приложение BasaltMiner.<br>

    Я создал неофициальную версию не с целью украсть чью-то идею.<br>
    Причина - официальная версия не работает долгое время (на момент написания этого текста (06.10.2021) всё ещё не работает) + хочется поиграть, например, только с друзьями.<br>
    Сервер написан на python с нуля. Клиентская часть никак не изменена (кроме исправления нескольких багов).<br>
    Официальная версия выйдет до апреля.<br><br>

    Разработчик неоф версии:<br>
     - discord: Ruslan#9204<br>
     - twitch: ruslan_uc<br><br>

    Разработчики офиц. версии (twitch):<br>
     - LiphiTC<br>
     - Sawer_<br>
     <br>
     <a href="/dev">Информация о сервере (неоф. версии)</a><br><br>
     Изменения в новой (официальной) версии:<br>
     Обновлён дизайн.<br>
     Более отзывчивый интерфейс.<br>
     Добавлены 3 новые шахты с метатиками 1.18.<br>
     Обновлена дуэльная система.<br>
     <br>
     Исходный код сервера: <a href="https://github.com/RuslanUC/BasaltMiner-server">BasaltMiner-server</a><br>
     Исходный код андроид-клиента: <a href="https://github.com/RuslanUC/BasaltMiner-android">BasaltMiner-android</a>
"""

dev = """
	<h1>Информация о сервере (неоф. версии)</h1>
        (Во всех запросах должен быть заголовок "X-Extension-Jwt" с токеном авторизации)
        <table border="1">
        <caption>Список url c описанием</caption>
        <tr>
          <th>Путь</th>
          <th>Описание</th>
          <th>Что возвращает</th>
          <th>Пример возвращаемых данных</th>
        </tr>
        <tr>
          <td>/ext/auth</td>
          <td>авторизация</td>
          <td>Уровень, id шахты, время разрушения блока (мс), count, id блока, время обновления, золото, редстоун</td>
          <td>{"level": 1, "world": 1, "time": 3000, "count": 1634217527157, "block": 1, "point": 2, "update": {"time": 1634217527576, "money": 10, "points": 5000}}</td>
        </tr>
        <tr>
          <td>/mine/reward</td>
          <td>награда за блок</td>
          <td>Блок, время разрушения блока, цена за блок, буст, время обновления, золото, редстоун</td>
          <td>{"block": 1, "point": 2, "time": 3000, "cost": 0.1, "boost": 1, "update": {"time": 1634217527576, "money": 10.1, "points": 5000}}</td>
        </tr>
        <tr>
          <td>/upgrade/update</td>
          <td>обновление данных</td>
          <td>Время обновления, золото, редстоун</td>
          <td>{"time": 1634217527576, "money": 10.1, "points": 5000}</td>
        </tr>
        <tr>
          <td>/upgrade/income</td>
          <td>информация о бусте, доходе со стримеров</td>
          <td>Буст, общий множитель, доход со стримеров</td>
          <td>{"boost": [["Постоянный множитель", 1.2]], "total": 1.2, "income": 0}</td>
        </tr>
        <tr>
          <td>/upgrade/level</td>
          <td>информация об уровне</td>
          <td>Уровень, биба, характеристики, цена сброса, очки характеристик</td>
          <td>{"level": [1, 10], "biba": [0, 2500, 0, 100], "stats": [["Сила", 0, 0], ["Ловкость", 0, 0], ["Интеллект", 0, 0], "discost": 1000, "statpoints": 1}</td>
        </tr>
        <tr>
          <td>/upgrade/levelup</td>
          <td>повышение уровня</td>
          <td>Код ответа (1 - всё нормально, 2 - недостаточно золота), цена, время разрушения блока, время обновления, золото, редстоун</td>
          <td>{"code": 1, "cost": [2, 30], "time": 2750, "update": {"time": 1634217527576, "money": 0.1, "points": 5000}}</td>
        </tr>
        <tr>
          <td>/upgrade/bibaup</td>
          <td>прокачка бибы</td>
          <td>Код ответа (1 - всё нормально, 2 - недостаточно редстоуна), цена, время обновления, золото, редстоун</td>
          <td>{"code": 1, "cost": [1, 2500, 0, 95], "update": {"time": 1634217527576, "money": 10.1, "points": 2500}}</td>
        </tr>
        <tr>
          <td>/upgrade/statdis</td>
          <td>сброс характеристик</td>
          <td>Код ответа (1 - всё нормально, 2 - нечего сбрасывать, 3 - недостаточно редстоуна), очки характеристик, время обновления, золото, редстоун, цена сброса</td>
          <td>{"code": 1, "statpoints": 1, "update": {"time": 1634217527576, "money": 10.1, "points": 2500, "cost": 1000}}</td>
        </tr>
        <tr>
          <td>/upgrade/statadd</td>
          <td>улучшение характеристик</td>
          <td>Код ответа (1 - всё нормально, 2 - недостаточно очков характеристик), характеристики, очки характеристик</td>
          <td>{"code": 1, "stats": [["Сила", 0, 1], ["Ловкость", 0, 0], ["Интеллект", 0, 0], "statpoints": 0}</td>
        </tr>
        <tr>
          <td>/upgrade/faq</td>
          <td>FAQ</td>
          <td>Вопросы и ответы</td>
          <td>[["Вопрос", "Ответ"]]</td>
        </tr>
        <tr>
          <td>/top/list</td>
          <td>список топа</td>
          <td>Топ по золоту, редстоуну, победам и т.д.</td>
          <td>[[["ruslan_uc", 2]], [["ruslan_uc", 0.1]], [["ruslan_uc", 0]], [["ruslan_uc", 0]], [["ruslan_uc", 0]]]</td>
        </tr>
        <tr>
          <td>/world/list</td>
          <td>список шахты</td>
          <td>Шахты</td>
          <td>[[1, "Земля", "5D8052"], [3], [5], [8], [13], [16]]</td>
        </tr>
        <tr>
          <td>/world/select</td>
          <td>выбор шахты</td>
          <td>Время разрушения блока, блок</td>
          <td>{"point": 2, "time": 2500, "block": 1}</td>
        </tr>
        <tr>
          <td>/duel/menu</td>
          <td>меню дуели</td>
          <td>Победы, колво дуелей, автоматически принимать дуели, принимать случайные дуели, запросы, результаты</td>
          <td>{"wins": 0, "count": 0, "auto": false, "rnd": false, "requests": [], "myrequests": [], "results": []}</td>
        </tr>
        <tr>
          <td>/duel/set</td>
          <td>изменить настройки</td>
          <td>Ничего</td>
          <td>{"ok": True}</td>
        </tr>
        <tr>
          <td>/duel/rnd</td>
          <td>дуель со случайным игроком</td>
          <td>Код ответа (1 - слишком много дуелей, 2 - не найдено подходящих игроков. 3 - всё нормально), результат (ваш ник, ник оппонента, дата и время, победа)</td>
          <td>{"code": 3, "result": ["ruslan_uc", "dev_ruslan_uc", "14.10.2021-16:55:30", true]}</td>
        </tr>
        <tr>
          <td>/duel/send</td>
          <td>отправка предложения дуели</td>
          <td>Код ответа (1 - ник не подходит, 2 - нельзя отправить запрос самому себе, 3 - у оппонента уровень ниже 9, 4 - вы уже отправили запрос этому игроку, 5 - слишком много дуелей, 6 - всё нормально), результат (ваш ник, ник оппонента, дата и время)</td>
          <td>{"code": 6, "request": ["ruslan_uc", "dev_ruslan_uc", "14.10.2021-16:55:30"]}</td>
        </tr>
        <tr>
          <td>/duel/decline</td>
          <td>отмена запроса</td>
          <td>Ничего</td>
          <td>{"ok": True}</td>
        </tr>
        <tr>
          <td>/duel/accept</td>
          <td>принять запрос</td>
          <td>Кот ответа (2,3 - слишком много дуелей, 4 - слишком много дуелей с этим игроком, 5 - всё нормально), результат (ваш ник, ник оппонента, дата и время, победа), победы, кол-во дуелей</td>
          <td>{"code": 5, "result": ["ruslan_uc", "dev_ruslan_uc", "14.10.2021-16:55:30", true], "wins": 1, "count": 2}</td>
        </tr>
        <tr>
          <td>/upgrade/list</td>
          <td>список стримеров</td>
          <td>ID, уровень, имя, цена, редстоун, доход сейчас, доход после прокачки</td>
          <td>[[0, 0, "5opka", "1M", 0, 0, "1K"],[1, 0, "JackLooney", "100M", 100, 0, "10K"],[2, 0, "exx1dae", "10B", 250, 0, "100K"],[3, 0, "Zakviel", "10T", 500, 0, "10M"]]</td>
        </tr>
        <tr>
          <td>/upgrade/streamerup</td>
          <td>прокачка стримеров</td>
          <td>Код ответа (1 - недостаточно золота, 2 - недостаточно редстоуна, 3 - всё нормально), список стримеров, время обновления, золото, редстоун</td>
          <td>{"code": 3, "info": [...], "update": {"time": 1634217527576, "money": 0.1, "points": 5000}}</td>
        </tr>
        </table>
        <br>
        <table border="1">
        <caption>Числа и их сокращённые значения</caption>
        <tr>
          <th>Сокращённое значение</th>
          <th>Полное число</th>
        </tr>
        <tr>
          <td>1K</td>
          <td title="1000">10<sup>3</sup></td>
        </tr>
        <tr>
          <td>1M</td>
          <td title="1000000">10<sup>6</sup></td>
        </tr>
        <tr>
          <td>1B</td>
          <td title="1000000000">10<sup>9</sup></td>
        </tr>
        <tr>
          <td>1T</td>
          <td title="1000000000000">10<sup>12</sup></td>
        </tr>
        <tr>
          <td>1Q</td>
          <td title="1000000000000000">10<sup>15</sup></td>
        </tr>
        <tr>
          <td>1E</td>
          <td title="1000000000000000000">10<sup>18</sup></td>
        </tr>
        <tr>
          <td>1Z</td>
          <td title="1000000000000000000000">10<sup>21</sup></td>
        </tr>
        <tr>
          <td>1Y</td>
          <td title="1000000000000000000000000">10<sup>24</sup></td>
        </tr>
        <tr>
          <td>1O</td>
          <td title="1000000000000000000000000000">10<sup>27</sup></td>
        </tr>
        </table>
        <br>
        <h1>Информация о базе данных</h1>
        БД: MySQL<br>
        SQL код таблиц:<br>
        &nbsp;&nbsp;DROP TABLE IF EXISTS `users`;<br>
        &nbsp;&nbsp;CREATE TABLE `users` (<br>
        &nbsp;&nbsp;  `user_id` bigint not null,<br>
        &nbsp;&nbsp;  `login` longtext not null,<br>
        &nbsp;&nbsp;  `count` bigint not null,<br>
        &nbsp;&nbsp;  `level` bigint not null default 1,<br>
        &nbsp;&nbsp;  `gold` double not null default 0,<br>
        &nbsp;&nbsp;  `redstone` bigint not null default 0,<br>
        &nbsp;&nbsp;  `boost` double not null default 1.0,<br>
        &nbsp;&nbsp;  `breakTime` bigint not null default 1500,<br>
        &nbsp;&nbsp;  `block` bigint not null default 1,<br>
        &nbsp;&nbsp;  `world` bigint not null default 1,<br>
        &nbsp;&nbsp;  `duelsTotal` bigint not null default 0,<br>
        &nbsp;&nbsp;  `duelsWins` bigint not null default 0,<br>
        &nbsp;&nbsp;  `duelsAuto` boolean not null default false,<br>
        &nbsp;&nbsp;  `duelsRandom` boolean not null default false,<br>
        &nbsp;&nbsp;  `statPoints` bigint not null default 0,<br>
        &nbsp;&nbsp;  `stats` longtext not null default "[0, 0, 0]",<br>
        &nbsp;&nbsp;  `streamers` longtext not null default "[0, 0, 0, 0]",<br>
        &nbsp;&nbsp;  `lastupdate` bigint not null default 0,<br>
        &nbsp;&nbsp;  `biba` bigint not null default 0,<br>
        &nbsp;&nbsp;  `ban` boolean not null default false,<br>
        &nbsp;&nbsp;  `banReason` longtext not null default "",<br>
        &nbsp;&nbsp;  UNIQUE KEY `user_id` (`user_id`) USING HASH<br>
        &nbsp;&nbsp;) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;<br>
        &nbsp;&nbsp;<br>
        &nbsp;&nbsp;DROP TABLE IF EXISTS `duels`;<br>
        &nbsp;&nbsp;CREATE TABLE `duels` (<br>
        &nbsp;&nbsp;  `user1` bigint not null,<br>
        &nbsp;&nbsp;  `user2` bigint not null,<br>
        &nbsp;&nbsp;  `winner` bigint not null,<br>
        &nbsp;&nbsp;  `completed` boolean not null,<br>
        &nbsp;&nbsp;  `time` bigint not null<br>
        &nbsp;&nbsp;) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;<br>
        <br>
        Исходный код сервера: <a href="https://github.com/RuslanUC/BasaltMiner-server">BasaltMiner-server</a><br>
        Исходный код андроид-клиента: <a href="https://github.com/RuslanUC/BasaltMiner-android">BasaltMiner-android</a>
"""