from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Input, Analysis
from .forms import DocumentForm

# Create your views here.


def browse(request):
	
	# 보안 - 비로그인자 강제 리다이렉트
	if not request.user.is_authenticated:
		return redirect('/accounts/login/')

	objects = Input.objects.all().order_by('id').reverse()

	page = request.GET.get('page', 1)
	paginator = Paginator(objects, 5) #한 페이지 몇개?

	try:
		inputs = paginator.page(page)
	except PageNotAnInteger:
		inputs = paginator.page(1)
	except EmptyPage:
		inputs = paginator.page(paginator.num_pages)

	return render(request, 'aisle/browse.html', { 'inputs': inputs })

def upload(request):
	# 보안 - 비로그인자 강제 리다이렉트
	if not request.user.is_authenticated:
		return redirect('/accounts/login/')

	if request.method == 'POST':
		form = DocumentForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			calculate(None)
			return HttpResponse("Calc completed!")
	else:
		form = DocumentForm()
	
	return render(request, 'aisle/model_form_upload.html', {'form': form})


def calculate(request):

	import csv, os

	#일단 야메로 젤 최근꺼 1개 불러옴
	lastfile = Input.objects.order_by('id').last()

	# bay_to_aisle을 읽어서 딕셔너리를 만든다
	with open(os.getcwd() + lastfile.bay_to_aisle_file.url, newline='') as csvfile:
		bay_to_aisle = csv.reader(csvfile)
		bay_to_aisle_dict = {0:0}
		index = 0
		for row in bay_to_aisle:
			bay_to_aisle_dict[row[0]] = row[1]
			index += 1
			# if index == 100:
			# 	break

	# aisle_file을 읽어서 딕셔너리를 만든다
	with open(os.getcwd() + lastfile.aisle_file.url, newline='') as csvfile:
		aisle = csv.reader(csvfile)
		aisle_dict = {0:0}
		index = 0
		for row in aisle:
			aisle_dict[row[0]] = row[1]
			index += 1
			#if index == 100:
			#	break


	# log를 읽어와서, bay에 해당하는 aisle을 찾고, 해당 aisle에 수량을 더한다
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
				# 인테그리티 체크
				# print("################## ERROR ################# - BAY '{}'' is not in bay_to_aisle.csv".format(row[0]))
	
	# 인테그리티 체크				
	integrity_message = "[Bay_to_aisle.csv] {}% Integrity in total {} bay trials.".format(round(100*counter_okay/(counter_okay+counter_error),1), counter_okay+counter_error)
	#integrity_message = "[Bay_to_aisle.csv] {}% Integrity; Total {} bays tried, aisle matched {}, aisle unmatched {}. ".format(round(100*counter_okay/(counter_okay+counter_error),1), counter_okay+counter_error, counter_okay, counter_error)


	# current_list (['aisle','cost','quantity'])를 만든다
	aisle_list = list(aisle_counter_dict.keys())
	del(aisle_list[0])
	current_list = [ ['aisle','cost','quantity'] ]
	cost_aisle_list = [ [-1,-1] ]
	aisle_quantity_list = [ [-1,-1] ]
	current_total_cost = 0
	counter_okay = 0
	counter_error = 0


	for row in aisle_list:
		try:
			counter_okay += 1
			# aisle, cost, quantity
			current_list.append( [ row, float(aisle_dict[row]), int(aisle_counter_dict[row]) ] )
			cost_aisle_list.append( [float(aisle_dict[row]), row ] )
			aisle_quantity_list.append( [ row, int(aisle_counter_dict[row]) ] )
			current_total_cost = current_total_cost + float(aisle_dict[row]) * int(aisle_counter_dict[row])
		except:
			counter_error += 1
			#aisle.csv에 해당 aisle의 코스트 데이터가 없음
			#print("################## ERROR ################# - no cost data on {}".format(row))

	# 인테그리티 체크				
	integrity_message += "/ [Aisle.csv] {}% Integrity in total {} aisle trials. ".format(round(100*counter_okay/(counter_okay+counter_error),1), counter_okay+counter_error)
	#integrity_message += "/ [Aisle.csv] {}% Integrity; Total {} bays tried, aisle matched {}, aisle unmatched {}.".format(round(100*counter_okay/(counter_okay+counter_error),1), counter_okay+counter_error, counter_okay, counter_error)
	
	
	del(current_list[0])
	del(cost_aisle_list[0])
	del(aisle_quantity_list[0])

	# Cost 적은것부터 정렬
	cost_aisle_list = sorted(cost_aisle_list, key=lambda x:x[0])
	# Quantity 많은것부터 정렬
	aisle_quantity_list = sorted(aisle_quantity_list, key=lambda x:x[1], reverse=True)

	suggested_total_cost = 0
	#suggested_list = [ ['cost', 'aisle', 'suggested_aisle', 'suggested_quantity'] ]

	# DB 쓰기 - Analysis 테이블에 밀어넣는다
	for i in range(0, len(aisle_quantity_list)):
		#suggested_list.append( [ cost_aisle_list[i][0], cost_aisle_list[i][1], aisle_quantity_list[i][0], aisle_quantity_list[i][1]])
		Analysis(input = lastfile,
			cost_rank = i+1,
			cost = cost_aisle_list[i][0],
			aisle = cost_aisle_list[i][1],
			suggested_aisle = aisle_quantity_list[i][0],
			suggested_quantity = aisle_quantity_list[i][1]).save()
		suggested_total_cost = suggested_total_cost + cost_aisle_list[i][0]*aisle_quantity_list[i][1]

	#print("######################################################")
	#print("Current cost = {}, Optimized cost = {}".format(current_total_cost, suggested_total_cost))
	
	# DB에 분석결과 업데이트
	lastfile.integrity_check = integrity_message
	lastfile.current_total_cost = round(current_total_cost,1)
	lastfile.suggested_total_cost = round(suggested_total_cost,1)
	lastfile.save()


def result (request, input_id):
	
	# 보안 - 비로그인자 강제 리다이렉트
	if not request.user.is_authenticated:
		return redirect('/accounts/login/')

	input_object = Input.objects.get(pk=input_id)
	analyses = Analysis.objects.filter(input = input_object)

	current_aisle_dict = {0:[0,0]}
	
	rank = 1
	for row in analyses:
		current_aisle_dict[row.suggested_aisle] = [row.suggested_quantity, rank]
		rank += 1

	gap_max = 0
	temp_array = [ [0, 0, 0, 0, 0, 0, 0, 0, 0] ]
	for row in analyses:
		gap = abs(current_aisle_dict[row.aisle][1] - row.cost_rank)
		if gap_max < gap:
			gap_max = gap
		temp_array.append( [ row.cost_rank, round(row.cost,1), row.aisle, row.suggested_aisle, row.suggested_quantity, current_aisle_dict[row.aisle][0], current_aisle_dict[row.aisle][1], gap, 0 ] )
	del(temp_array[0])

	for row in temp_array:
		if ( row[7] / gap_max ) > 0.66:
			row[8] = 'red'
		elif ( row[7] / gap_max ) > 0.33:
			row[8] = 'yellow'
		else:
			row[8] = 'white'

	return render(request, 'aisle/result.html', { 'analyses': temp_array, 'input_object': input_object } )


# 페이지네이션 되는거	
def result_p (request):

	# 보안 - 비로그인자 강제 리다이렉트
	if not request.user.is_authenticated:
		return redirect('/accounts/login/')

	#일단 야메로 최근꺼 가져오기
	objects = Analysis.objects.filter(input = Input.objects.order_by('id').last())

	page = request.GET.get('page', 1)
	paginator = Paginator(objects, 20) #한 페이지 몇개?

	try:
		analyses = paginator.page(page)
	except PageNotAnInteger:
		analyses = paginator.page(1)
	except EmptyPage:
		analyses = paginator.page(paginator.num_pages)

	return render(request, 'aisle/result.html', { 'analyses': analyses })