-- Fictional training data only. Passwords cannot be used until CLI initialization.
-- OR IGNORE makes repeated demo initialization non-destructive.
INSERT OR IGNORE INTO Roles(code, name) VALUES
 ('admin','Администратор'),('operator','Оператор'),
 ('technician','Исполнитель'),('applicant','Заявитель');
INSERT OR IGNORE INTO Users(id, username, name, role_code) VALUES
 (1,'admin','Администратор','admin'),(2,'operator','Оператор','operator'),
 (3,'tech1','Мастер 1','technician'),(4,'tech2','Мастер 2','technician'),
 (5,'barista1','Бариста 1','applicant'),(6,'barista2','Бариста 2','applicant');
INSERT OR IGNORE INTO Cafes(id, name, address) VALUES
 (1,'Центр','Учебная локация 1'),(2,'Парк','Учебная локация 2'),(3,'Вокзал','Учебная локация 3');
INSERT OR IGNORE INTO Categories(id, name) VALUES
 (1,'Сантехника'),(2,'Кофейное оборудование'),(3,'Электрика'),
 (4,'Мебель'),(5,'Хозяйственные работы');
INSERT OR IGNORE INTO Statuses(code, name, sort_order) VALUES
 ('new','Новая',1),('in_progress','В работе',2),('done','Выполнена',3),('closed','Закрыта',4);
INSERT OR IGNORE INTO Requests(id,title,description,cafe_id,category_id,status_code,applicant_id,assignee_id,priority) VALUES
 (1,'Протекает кран у мойки','Вода подтекает у основания крана рабочей мойки. Требуется заменить уплотнение.',1,1,'new',5,NULL,'high'),
 (2,'Кофемашина не набирает давление','При приготовлении эспрессо давление не поднимается до рабочего уровня.',2,2,'new',6,NULL,'urgent'),
 (3,'Не горит свет над стойкой','Перестал работать светильник над барной стойкой, необходимо проверить питание.',3,3,'in_progress',5,4,'normal'),
 (4,'Закрепить ножку стула','Стул у окна шатается. Крепёж проверен и подтянут исполнителем.',1,4,'done',6,3,'low'),
 (5,'Прочистить слив у мойки','Вода медленно уходит из мойки, периодически появляется неприятный запах.',2,1,'new',5,NULL,'high'),
 (6,'Обслужить кофемолку','Нестабильный помол, нужно проверить жернова и выполнить настройку.',1,2,'in_progress',5,3,'normal'),
 (7,'Заменить лампу в подсобке','Лампа освещения подсобного помещения перегорела во время вечерней смены.',3,3,'new',6,NULL,'normal'),
 (8,'Починить дверцу шкафа','Петля дверцы шкафа для посуды закреплена, требуется проверить результат.',2,4,'done',6,3,'low'),
 (9,'Заказать хозяйственное обслуживание','Нужна плановая уборка технической зоны после перемещения оборудования.',1,5,'new',5,NULL,'low'),
 (10,'Проверить розетку у холодильника','Розетка у холодильника нагревается. Оборудование отключено до осмотра мастером.',3,3,'in_progress',6,4,'urgent'),
 (11,'Устранить течь сифона','Под мойкой обнаружена небольшая течь в соединении сифона, поставлена ёмкость.',2,1,'in_progress',5,3,'high'),
 (12,'Заменить уплотнение холодильника','Уплотнение заменено, температура стабильна, результат принят оператором.',1,5,'closed',6,3,'normal');
INSERT OR IGNORE INTO Comments(id,request_id,author_id,body) VALUES
 (1,1,5,'Заметили протечку в начале утренней смены.'),
 (2,3,4,'Проверяю светильник, линия освещения отключена.'),
 (3,4,3,'Крепление подтянуто, стул устойчив.'),
 (4,10,2,'До осмотра не включать оборудование в эту розетку.'),
 (5,12,2,'Результат проверен, заявка закрыта.');
INSERT OR IGNORE INTO RequestHistory(id,request_id,actor_id,event,new_value)
 SELECT id,id,applicant_id,'seeded',status_code FROM Requests WHERE id BETWEEN 1 AND 12;
