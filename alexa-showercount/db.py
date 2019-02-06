
import pymysql

connection = pymysql.connect(host='localhost',user='root',password='123456789', db='pythonDB')

a = "erdinc"
b = 23423
c = 234234234

'''
with connection.cursor() as cursor:
	sql = "INSERT INTO timeAlexa (id, sTime, eTime) VALUES (%s, %s, %s);"
	cursor.execute(sql, (a, int(b), int(c)))
	print("Task added successfully")
	connection.commit()
'''



with connection.cursor() as cursor:
	sql = "SELECT * FROM timeAlexa WHERE id = 'erdinc'"
	cursor.execute(sql)
	result = cursor.fetchall()
	if not result:
		print("EMPTY")	
