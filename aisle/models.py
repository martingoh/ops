from django.db import models

# Create your models here.


class Log(models.Model):
	aisle = models.CharField(max_length=255)
	cost = models.FloatField()

class Input(models.Model):
    description = models.CharField(max_length=255, blank=True)
    fc_code = models.CharField(max_length=255, blank=True)
    user_id = models.CharField(max_length=255, blank=True)
    
    log_file = models.FileField(upload_to='documents/')
    aisle_file = models.FileField(upload_to='documents/')
    bay_to_aisle_file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Output_asis(models.Model):

	input = models.ForeignKey('Input', on_delete=models.PROTECT)
	cost_rank = models.IntegerField()
	cost = models.FloatField()
	aisle = models.CharField(max_length=255)
	quantity = models.IntegerField()
	quantity_rank = models.IntegerField()
	#등수아일, 코스트 : 현재 아일, 현재 퀀티티, 토탈 코스트 / 바뀐 아일, 바뀐 퀀티티, 바뀐 토탈 코스트  
	#
	#
	#