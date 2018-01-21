from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from .models import Input
from .forms import DocumentForm

# Create your views here.

def index (request):	

	return HttpResponse("Hello! Martin!")

def upload (request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            #세이브 후 리다이렉트 되는 곳임 -> 추후 인테그리티 체크하면 될듯
            return redirect('/viewresult')
    else:
        form = DocumentForm()
    return render(request, 'aisle/model_form_upload.html', {
        'form': form
    })

def viewresult (request):
	
	import csv, os

	#나중에는 유저 아이디까지 같이 고려해서 불러오면 될듯, 지금은 일단 야메로 라스트 1개 불러옴
	lastfile = Input.objects.order_by('id').last()

	# STEP 1. bay_to_aisle을 읽어서 딕셔너리를 만든다
	with open(os.getcwd() + lastfile.bay_to_aisle_file.url, newline='') as csvfile:
		bay_to_aisle = csv.reader(csvfile)
		bay_to_aisle_dict = {0:0}
		index = 0
		for row in bay_to_aisle:
			bay_to_aisle_dict[row[0]] = row[1]
			index += 1
			# if index == 100:
			# 	break

	# STEP 2. aisle_file을 읽어서 딕셔너리를 만든다
	with open(os.getcwd() + lastfile.aisle_file.url, newline='') as csvfile:
		aisle = csv.reader(csvfile)
		aisle_dict = {0:0}
		index = 0
		for row in aisle:
			aisle_dict[row[0]] = row[1]
			index += 1
			#if index == 100:
			#	break


	# STEP 3. log를 읽어와서
		# 3-1. bay에 해당하는 aisle을 찾고, 해당 aisle에 수량을 더한다
		# 3-2. 완료 후, 해당 aisle의 cost와 수량을 곱해서 total cost를 구한다
	
	#3-1
	with open(os.getcwd() + lastfile.log_file.url, newline='') as csvfile:
		logs = csv.reader(csvfile)
		aisle_counter_dict = {0:0}
		index = 0
		counter_okay = 0
		counter_error = 0

		for row in logs:
			try:
				counter_okay += 1
				aisle_name = bay_to_aisle_dict[row[0]]
				try:
					aisle_counter_dict[aisle_name] += int(row[1])
				except:
					aisle_counter_dict[aisle_name] = int(row[1])
			except:
				counter_error += 1
				#없는 bay이름이므로, 추후 로그처리
				#print("ERROR - BAY '{}'' is not in bay_to_aisle.csv".format(row[0]))
			
			
	print("*****************")
	print("Total {} logs : aisle matched {}, unmatched {}".format(counter_okay+counter_error, counter_okay,counter_error))
	print("*****************")
	# print(aisle_counter_dict)
	# print("*****************")

	# SORTING
	cost_rank_list = [ [-1,-1] ]
	quantity_rank_list = [ [-1,-1] ]
	asis_list = [ ['aisle','cost','quantity'] ]

	aisle_list = aisle_counter_dict.keys()
	for row in aisle_list:
		try:
			#print("Aisle {} / Cost {} / Quantity {}".format(row, aisle_dict[row], aisle_counter_dict[row]))
			asis_list.append( [ row, float(aisle_dict[row]), int(aisle_counter_dict[row]) ] )
			cost_rank_list.append( [row, float(aisle_dict[row])] )
			quantity_rank_list.append( [row, int(aisle_counter_dict[row]) ] )
		except:
			#aisle.csv에 해당 aisle의 코스트 데이터가 없음
			print("################## ERROR ################# - no cost data on {}".format(row))


	print("#############")
	print(asis_list)

	#cost_rank_list = sorted(cost_rank_list, key=lambda list:list[1])
	#quantity_rank_list = sorted(quantity_rank_list, key=lambda list:list[1])
	
	#print(cost_rank_list)
	#print(quantity_rank_list)
	
	
	#print(sorted(quantity_rank_dict.values()))


	#랭킹 만들기

# input = models.ForeignKey('Input', on_delete=models.PROTECT)
# 	cost_rank = models.IntegerField()
# 	cost = models.FloatField()
# 	aisle = models.CharField(max_length=255)
# 	quantity = models.IntegerField()
# 	quantity_rank = models.IntegerField()
	

	# STEP 4. 이제 데이터를 다 구했다
		# 랭킹을 계산한다. 코스트의 랭킹과, 퀀티티 랭킹을 계산한다
		# 이상향은, 코스트가 적은 순서대로, 대량 퀀티티를 배치하는 것이다
		# 루프를 돌려서, 코스트가 적은 아일명 : 퀀티티가 큰 아일명 - 뽑으면 될듯
		# 등수아일, 코스트 : 현재 아일, 현재 퀀티티, 토탈 코스트 / 바뀐 아일, 바뀐 퀀티티, 바뀐 토탈 코스트  



	return HttpResponse("CSV Printed!")