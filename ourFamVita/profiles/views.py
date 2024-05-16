from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
from datetime import datetime
from profiles.forms import Survey1Form, Survey2Form, Survey3Form, ProfileInfo
from users.models import User, Profile, Survey, SurveyAllergy, SurveyDisease, SurveyFunction, AllergyCode, DiseaseCode, FunctionCode
# from django.db import transaction
from django.utils import timezone

def profile(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('/')
    else:
        user = User.objects.get(pk=user_id)

        profiles = Profile.objects.filter(custom_user_id=user_id, profile_status='activate')
        profile_count = profiles.count()
        context = {'profiles':profiles, "user": user, "profile_count": profile_count}
    return render(request, 'profiles/profile.html', context)



def profile_delete(request, profile_id):
    if request.method == 'POST':
        profile = Profile.objects.get(profile_id=profile_id)
        profile.profile_status = 'deactivate'
        profile.save()
        return redirect('/profiles/')



def survey1(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('/')
    if request.method == 'POST':
        form = Survey1Form(request.POST)
        if form.is_valid():
            user = User.objects.get(pk=user_id)

            profile = Profile()
            profile.profile_name = form.cleaned_data['name']
            profile.profile_birth = form.cleaned_data['birth']
            profile.custom_user_id = user
            profile.save()

            # 프로필ID를 세션에 저장
            request.session["profile_id"] = profile.profile_id

            profile_id = request.session.get('profile_id')
            profile = Profile.objects.get(pk=profile_id)

            survey = Survey()
            survey.custom_user_id = user
            survey.profile_id = profile
            survey.survey_sex = form.cleaned_data['sex']
            # print(survey.survey_sex)
            if survey.survey_sex == 'm':
                if form.cleaned_data['pregnancy'] == 'P0':
                    survey.survey_pregnancy_code = form.cleaned_data['pregnancy']
                    survey.save()
                else:
                    form.add_error("pregnancy", "임신 상태를 확인해 주세요.")
                    context = {'form':form}
                    return render(request, 'profiles/survey1.html', context)
            else:
                survey.survey_pregnancy_code = form.cleaned_data['pregnancy']
                survey.save()

            # 만나이 계산
            profile_birth = str(profile.profile_birth)
            birth = datetime.strptime(profile_birth, '%Y-%m-%d').date()
            today = datetime.now().date()
            age = today.year - int(profile_birth[:4])
            ## 생일이 있는 달을 아직 안 지남
            if today.month < birth.month:
                age -= 1

            ## 현재 월이 생일이 있는 달이지만 생일 일자가 아직 안 지남
            elif today.month == birth.month and today.day < birth.day:
                age -= 1
            
            if age >= 6:
                if age <=8:
                    survey.survey_age_group = '6~8세'
                elif age <= 11:
                    survey.survey_age_group = '9~11세'
                elif age <= 14:
                    survey.survey_age_group = '12~14세'
                elif age <= 18:
                    survey.survey_age_group = '15~18세'
                elif age <= 29:
                    survey.survey_age_group = '20대'
                elif age <= 39:
                    survey.survey_age_group = '30대'
                elif age <= 49:
                    survey.survey_age_group = '40대'
                elif age <= 59:
                    survey.survey_age_group = '50대'
                elif age <= 69:
                    survey.survey_age_group = '60대'
                elif age <= 79:
                    survey.survey_age_group = '70대'
                elif age >= 80:
                    survey.survey_age_group = '80세 이상'
                
            else:
                form.add_error("birth", "만 6세 미만은 서비스 이용이 불가합니다.")
                context = {'form':form}
                return render(request, 'profiles/survey1.html', context)

            survey.save()

            # 서베이ID를 세션에 저장
            request.session["survey_id"] = survey.survey_id

            survey_id = request.session.get('survey_id')
            survey = Survey.objects.get(pk=survey_id)

            allergy_codes = form.cleaned_data['allergy']
            # 기본키가 동작하는 AllergyCode에 넣고 >> 외래키가 동작하는 SurveyAllergy에 넣기
            for allergy_code in allergy_codes:
                allergy_instance = AllergyCode.objects.get(allergy_code=allergy_code)
                SurveyAllergy.objects.create(survey_id=survey,
                                               allergy_code=allergy_instance)
            return redirect('/profiles/survey-2/')
    else:
        form = Survey1Form()
    context = {'form': form}
    return render(request, 'profiles/survey1.html', context)



def survey2(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('/')
    if request.method == 'POST':
        form = Survey2Form(request.POST)
        if form.is_valid():
            # 유저, 프로필, 서베이 세션 가져오기
            survey_id = request.session.get('survey_id')            
            survey = Survey.objects.get(pk=survey_id)

            function_codes = form.cleaned_data['function']
            if not function_codes:
                function_codes = ['HF00']

            if len(function_codes) <= 5:
                if survey.survey_sex == 'f':
                    if ('HF13' in function_codes) or ('HF14' in function_codes):
                        form.add_error("function", "전립선, 남성 건강 선택 불가 대상입니다.")
                        context = {'form': form}
                        return render(request, 'profiles/survey2.html', context)
                if survey.survey_sex == 'm':
                    if ('HF15' in function_codes) or ('HF16' in function_codes):
                        form.add_error("function", "여성 갱년기, 여성 건강 선택 불가 대상입니다.")
                        context = {'form': form}
                        return render(request, 'profiles/survey2.html', context)
                if not ('6~8세' in survey.survey_age_group) or ('9세~11세' in survey.survey_age_group):            
                    if function_codes == ['HF21']:
                        form.add_error("function", "어린이 성장 선택 불가 대상입니다.")
                        context = {'form': form}
                        return render(request, 'profiles/survey2.html', context)
                for function_code in function_codes: 
                    function_instance = FunctionCode.objects.get(function_code=function_code)
                    SurveyFunction.objects.create(survey_id=survey,
                                                      function_code=function_instance)
                return redirect('/profiles/survey-3/')            
            else:
                form.add_error("function", "최대 선택 수를 초과하였습니다.")
                context = {'form': form}
                return render(request, 'profiles/survey2.html', context)
    else:
        form = Survey2Form()
    context = {'form': form}
    return render(request, 'profiles/survey2.html', context)



def survey3(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('/')
    if request.method == 'POST':
        form = Survey3Form(request.POST)
        if form.is_valid():
            user = User.objects.get(pk=user_id)

            profile_id = request.session.get('profile_id')
            profile = Profile.objects.get(pk=profile_id)  

            survey_id = request.session.get('survey_id')
            survey = Survey.objects.get(pk=survey_id)
            survey.custom_user_id = user
            survey.profile_id = profile
            survey.survey_height = form.cleaned_data['height']
            survey.survey_weight = form.cleaned_data['weight']
            survey.survey_smoke = form.cleaned_data['smoke']
            if not survey.survey_smoke:
                survey.survey_smoke = '9'            
            survey.survey_alcohol_code = form.cleaned_data['alcohol']
            if not survey.survey_alcohol_code:
                survey.survey_alcohol_code = 'A9'  
            survey.survey_operation_code = form.cleaned_data['operation']
            if not survey.survey_operation_code:
                survey.survey_operation_code = 'O9'  
            survey.save()

            disease_codes = form.cleaned_data['disease']
            if not disease_codes:
                disease_codes = ['DI00']
                # return redirect('/profiles/')
            if len(disease_codes) <= 5: 
                for disease_code in disease_codes:
                    # 기본키가 동작하는 DiseaseyCode에 넣고 >> 외래키가 동작하는 SurveyDisease에 넣기
                    disease_instance = DiseaseCode.objects.get(disease_code=disease_code)
                    # print(f'code: {disease_code}')
                    # print(f'codes: {disease_codes}')
                    survey_disease = SurveyDisease(
                        survey_id=survey,
                        disease_code=disease_instance
                    )
                    survey_disease.save()
                return redirect('/profiles/')
            else:
                form.add_error("disease", "최대 선택 수를 초과하였습니다.")
                context = {'form': form}
                return render(request, 'profiles/survey3.html', context)
    else:
        form = Survey3Form()
    context = {'form': form}
    return render(request, 'profiles/survey3.html', context)



# def profile_info(request, profile_id):
#     survey = get_object_or_404(Survey, pk=survey_id)
#     user_id = request.session.get('user')

#     if not user_id:
#         return redirect('/')

#     print(f'profile_id1: {profile_id}')
#     print(f'user_id1: {user_id}')

#     if request.method == 'POST':
#         form = Survey1Form(request.POST, instance=survey)

#         print(f'profile_id2: {profile_id}')
#         print(f'user_id2: {user_id}')

#         if form.is_valid():
#             user = User.objects.get(pk=user_id)

#             print(f'user: {user}')

#             # Profile 모델 인스턴스
#             profile = Profile.objects.get(pk=profile_id)
#             profile.profile_name = form.cleaned_data['name']
#             profile.profile_birth = form.cleaned_data['birth']
#             # 만나이 계산
#             profile_birth = str(profile.profile_birth)
#             birth = datetime.strptime(profile_birth, '%Y-%m-%d').date()
#             today = datetime.now().date()
#             age = today.year - int(profile_birth[:4])
#             if today.month < birth.month:
#                 age -= 1
#             elif today.month == birth.month and today.day < birth.day:
#                 age -= 1            
#             if age >= 6:
#                 if age <=8:
#                     survey.survey_age_group = '6~8세'
#                 elif age <= 11:
#                     survey.survey_age_group = '9~11세'
#                 elif age <= 14:
#                     survey.survey_age_group = '12~14세'
#                 elif age <= 18:
#                     survey.survey_age_group = '15~18세'
#                 elif age <= 29:
#                     survey.survey_age_group = '20대'
#                 elif age <= 39:
#                     survey.survey_age_group = '30대'
#                 elif age <= 49:
#                     survey.survey_age_group = '40대'
#                 elif age <= 59:
#                     survey.survey_age_group = '50대'
#                 elif age <= 69:
#                     survey.survey_age_group = '60대'
#                 elif age <= 79:
#                     survey.survey_age_group = '70대'
#                 elif age >= 80:
#                     survey.survey_age_group = '80세 이상'
                
#             else:
#                 form.add_error("birth", "만 6세 미만은 서비스 이용이 불가합니다.")

#             profile.custom_user_id = user
#             profile.save()

            
#             survey_id = request.session.get('survey_id')
#             # Survey 모델 인스턴스
#             survey = Survey.objects.get(pk=survey_id)
#             survey.custom_user_id = user
#             survey.profile_id = profile
#             survey.survey_sex = form.cleaned_data['sex']
#             if survey.survey_sex == 'm':
#                 if form.cleaned_data['pregnancy'] == 'P0':
#                     survey.survey_pregnancy_code = form.cleaned_data['pregnancy']
#                     survey.save()
#                 else:
#                     form.add_error("pregnancy", "임신 상태를 확인해 주세요.")
#                     context = {'form':form}
#                     return render(request, 'profiles/survey1.html', context)

#             survey.survey_pregnancy_code = form.cleaned_data['pregnancy']
#             survey.survey_height = form.cleaned_data['height']
#             survey.survey_weight = form.cleaned_data['weight']
#             survey.survey_smoke = form.cleaned_data['smoke']
#             survey.survey_alcohol_code = form.cleaned_data['alcohol']
#             survey.save()

#             # Allergy 모델 인스턴스
#             allergy_codes = form.cleaned_data['allergy']
#             for allergy_code in allergy_codes:
#                 allergy_instance = AllergyCode.objects.get(allergy_code=allergy_code)
#                 survey_allergy = SurveyAllergy.objects.get(
#                     pk=survey_id,
#                     allergy_code=allergy_instance
#                 )
#                 survey_allergy.save()

#             # # Function 모델 인스턴스
#             # function_codes = form.cleaned_data['function']
#             # if not function_codes:
#             #     function_codes = ['HF00']
#             # if len(function_codes) <= 5:
#             #     for function_code in function_codes: 
#             #         # 기본키가 동작하는 AllergyCode에 넣고 >> 외래키가 동작하는 SurveyAllergy에 넣기
#             #         function_instance = FunctionCode.objects.get(function_code=function_code)
#             #         survey_function = SurveyFunction.objects.get(
#             #             pk=survey_id,
#             #             function_code=function_instance
#             #         )
#             #         survey_function.save()
#             # else:
#             #     form.add_error("function", "최대 선택 수를 초과하였습니다.")

#             # # Disease 모델 인스턴스
#             # disease_codes = form.cleaned_data['disease']
#             # if not disease_codes:
#             #     disease_codes = ['DI00']
#             # if len(disease_codes) <= 5: 
#             #     for disease_code in disease_codes:
#             #         disease_instance = DiseaseCode.objects.get(disease_code=disease_code)
#             #         survey_disease = SurveyDisease.objects.get(
#             #             pk=survey_id,
#             #             disease_code=disease_instance
#             #         )
#             #         survey_disease.save()
#             # else:
#             #     form.add_error("disease", "최대 선택 수를 초과하였습니다.")

#             context = {'form': form}
#             return render(request, '/profiles/', context)
#     else:
#         form = ProfileInfo(instance=survey)
#     context = {'form': form}
#     return render(request, 'profiles/profile_info.html', context)


def profile_info(request, profile_id):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('/')

    # survey_allergy = SurveyAllergy.objects.get(pk=survey_id)
    # survey_disease = SurveyDisease.objects.get(pk=survey_id)
    # survey_function = SurveyFunction.objects.get(pk=survey_id)

    if request.method == 'POST':
        form = ProfileInfo(request.POST)

        if form.is_valid():
            profile = Profile.objects.get(pk=profile_id)
            profile.profile_name = form.cleaned_data['name']
            profile.profile_birth = form.cleaned_data['birth']
            profile.save()

            survey_id = request.session.get('survey_id')
            
            # survey = Survey.objects.get(pk=survey_id)
            # survey.survey_sex = form.cleaned_data['sex']
            # survey.survey_height = form.cleaned_data['height']
            # survey.survey_weight = form.cleaned_data['weight']
            # survey.survey_smoke = form.cleaned_data['smoke']
            # survey.survey_alcohol_code = form.cleaned_data['alcohol']
            # survey.survey_operation_code = form.cleaned_data['operation']
            # survey.save()

            return redirect('/profiles')
    else:
        form = ProfileInfo()
    context = {'form': form}
    return render(request, 'profiles/profile_info.html', context)