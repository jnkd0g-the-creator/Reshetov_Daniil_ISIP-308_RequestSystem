-- Exercise data are rolled back: the public demo snapshot remains unchanged.
BEGIN;
-- Five independent INSERT statements.
INSERT INTO Cafes(id,name,address) VALUES(100,'Учебный бар SQL','Тестовая локация');
INSERT INTO Categories(id,name) VALUES(100,'Тестовая категория SQL');
INSERT INTO Users(id,username,name,role_code) VALUES(100,'sql_demo','SQL-пользователь','applicant');
INSERT INTO Requests(id,title,description,cafe_id,category_id,applicant_id) VALUES(100,'Проверка SQL','Проверка создания заявки запросом SQL.',100,100,100);
INSERT INTO Comments(id,request_id,author_id,body) VALUES(100,100,100,'Учебный комментарий SQL.');
-- Six SELECT; >=3 WHERE and >=2 JOIN.
SELECT id,title,status_code FROM Requests WHERE status_code='new' ORDER BY id;
SELECT id,title,priority FROM Requests WHERE priority='urgent' ORDER BY id;
SELECT id,title FROM Requests WHERE title LIKE '%кран%' ORDER BY id;
SELECT r.id,r.title,c.name AS cafe,cat.name AS category,s.name AS status
 FROM Requests r JOIN Cafes c ON c.id=r.cafe_id
 JOIN Categories cat ON cat.id=r.category_id JOIN Statuses s ON s.code=r.status_code
 WHERE r.archived=0 ORDER BY r.id;
-- LEFT JOIN intentionally preserves unassigned requests (correction of INNER JOIN draft).
SELECT r.id,r.title,u.name AS applicant,assignee.name AS assignee
 FROM Requests r JOIN Users u ON u.id=r.applicant_id
 LEFT JOIN Users assignee ON assignee.id=r.assignee_id ORDER BY r.id;
SELECT c.name,COUNT(r.id) AS request_count FROM Categories c
 LEFT JOIN Requests r ON r.category_id=c.id GROUP BY c.id ORDER BY c.id;
UPDATE Requests SET priority='high' WHERE id=100;
UPDATE Requests SET description='Уточнённое описание тестовой заявки SQL.' WHERE id=100;
DELETE FROM Comments WHERE id=100;
DELETE FROM Requests WHERE id=100;
ROLLBACK;
