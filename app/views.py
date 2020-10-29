from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.conf import settings
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView
from .models import Staff, Customer, GeneratedData, MatchedData, VisuallyMatchedData, ImportData
from .forms import CustomerSelectForm, UploadFileSelectForm, VisuallyMatchedDataCreateForm, ImportDataCreateForm
from datetime import datetime
import openpyxl,  os, csv, urllib.parse, re

UPLOAD_NOT_COMPLETED = 0
CSV_OUTPUT_COMPLETED = 1
VISUALLY_CONFIRMED = 2
IMPORT_DATA_OUTPUT_COMPLETED = 3


class LoginFormView(SuccessMessageMixin, LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        return reverse('top')

    def get_success_message(self, cleaned_data):
        return f'{self.request.user}でログインしました'


class HistoryListView(ListView):
    template_name = 'app/top.html'

    def get_queryset(self):
        return GeneratedData.objects.order_by('-status')

    def get_context_data(self, **kwargs):
        customer = Customer.objects.all()
        staff = Staff.objects.all()
        matched = MatchedData.objects.filter(created_date__lte=timezone.now()).order_by('-created_date')
        visually_matched = VisuallyMatchedData.objects.filter(created_date__lte=timezone.now()).order_by('-created_date')
        import_data = ImportData.objects.filter(created_date__lte=timezone.now()).order_by('-created_date')
        context = super().get_context_data(**kwargs)
        context['customer'] = customer
        context['staff'] = staff
        context['matched'] = matched
        context['visually_matched'] = visually_matched
        context['import_data'] = import_data


        return context


class GeneratedDataCreateView(CreateView):
    model = GeneratedData
    form_class = CustomerSelectForm
    template_name = 'app/customer_select.html'

    @transaction.atomic
    def form_valid(self, form):
        generated_data = form.save(commit=False)
        author = Staff.objects.get(author=self.request.user)
        generated_data.author = author
        generated_data.status = GeneratedData.UPLOAD_NOT_COMPLETED
        generated_data.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('upload', kwargs={'pk': self.object.pk})


class MatchedDataCreateView(CreateView):
    model = MatchedData
    template_name = 'app/upload.html'
    form_class = UploadFileSelectForm

    def get_context_data(self, **kwargs):
        generated_data_pk = self.kwargs['pk']
        generated_data = GeneratedData.objects.get(pk=generated_data_pk)
        context = super().get_context_data(**kwargs)
        context['generated_data'] = generated_data
        context['status'] = UPLOAD_NOT_COMPLETED

        return context

    @transaction.atomic
    def form_valid(self, form):
        matched_data = form.save(commit=False)
        author = Staff.objects.get(author=self.request.user)
        matched_data.author = author
        generated_data_pk = self.kwargs['pk']
        matched_data.generated_id = generated_data_pk
        matched_data.save()

        generated = GeneratedData.objects.get(pk=generated_data_pk)
        generated.status = GeneratedData.CSV_OUTPUT_COMPLETED
        generated.save()

        brycen_file_path = urllib.parse.unquote(matched_data.brycen_file.path)
        billing_file_path = urllib.parse.unquote(matched_data.billing_file.path)

        file_path = create_csv(brycen_file_path, billing_file_path)
        # print('file_path:{}'.format(file_path))

        # csv_createのfile_pathを取得し、file_pathからMatchedDataのmatched_data_fileフィールドに紐付け
        path_split = os.path.split(file_path)
        dir_name = path_split[0]
        file_name = path_split[1]
        dir_name_split = dir_name.split('/')
        dir_name_list = dir_name_split[6:]
        matched_data_file_dir = '/'.join(dir_name_list)
        matched_data_file_path = os.path.join(matched_data_file_dir, file_name)
        matched_data.matched_data_file = matched_data_file_path
        # print('matched_data_file_path:{}'.format(matched_data.matched_data_file))

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('matched_data_detail', kwargs={'pk': self.object.pk})


# 突合スクリプト
def create_csv(f, f2):
    BRYCEN_STORE_CODE_NUM = 1
    BRYCEN_PT_CODE_NUM = 2
    BRYCEN_UNIT_PRICE_NUM = 4
    BRYCEN_AMOUNT_NUM = 5
    BRYCEN_TOTAL_NUM = 7

    BILLING_STORE_CODE_NUM = 49
    BILLING_STORE_NAM_NUM = 50
    BILLING_DAY_NUM = 39
    BILLING_PT_CODE_NUM = 2
    BILLING_PT_NAM_NUM = 3
    BILLING_ITEM_CODE_NUM = 41
    BILLING_ITEM_NAM_NUM = 42
    BILLING_UNIT_PRICE_NUM = 43
    BILLING_UNIT_NUM = 44
    BILLING_AMOUNT_NUM = 45
    BILLING_TOTAL_NUM = 46
    BILLING_REMARK_NUM = 51

    BRYCEN_STORE_CODE_LIST_INDEX = 0
    BRYCEN_PT_CODE_LIST_INDEX = 1
    BRYCEN_TOTAL_LIST_INDEX = 4

    STORE_CODE_LIST_INDEX = 0
    PT_CODE_LIST_INDEX = 1
    TOTAL_LIST_INDEX = 4

    zenTOLL = 'トール'
    hanTOLL = 'ﾄｰﾙ'
    otherTOLL = '九州産交'

    wb = openpyxl.load_workbook(f)
    ws = wb.active
    greatest = ws.max_row

    # 契約データの必要情報を取得する
    brycen_data = []
    for row in ws.iter_rows(min_col=6, max_row=greatest + 1, max_col=15):
        if row[0].value:
            store = row[BRYCEN_STORE_CODE_NUM].value
            store_split = store.split(':')
            store_code = int(store_split[0])

            pt = row[BRYCEN_PT_CODE_NUM].value
            pt_split = pt.split(':')
            pt_code = int(pt_split[0])

            unit_price = row[BRYCEN_UNIT_PRICE_NUM].value
            unit_price = float(unit_price.replace(',', ''))

            amount = row[BRYCEN_AMOUNT_NUM].value
            amount = float(amount.replace(',', ''))

            total = row[BRYCEN_TOTAL_NUM].value
            total = int(total.replace(',', ''))

            brycen_list = [store_code, pt_code, unit_price, amount, total]
            brycen_data.append(brycen_list)

    file = open(f2)
    reader = csv.reader(file)
    data = list(reader)
    data.remove(data[0])

    # 電子請求データの必要情報を取得する　
    all_store_code = {'2493-1': '千葉支店', '2493-2': '板橋支店', '2493-3': '鹿島支店', '2493-4': '東京北支店', '2493-5': '東京支店',
                      '2493-6': '千葉南支店',
                      '2493-7': '土浦支店', '2493-8': '大宮支店', '2493-9': '熊谷支店', '2493-10': '市原支店', '2493-11': '東京中央支店',
                      '2493-12': '横浜支店',
                      '2493-13': '港北支店', '2493-14': '戸塚支店', '2493-15': '埼玉支店', '2493-17': '厚木支店', '2493-18': '青梅支店',
                      '2493-19': '平塚支店', '2493-20': '静岡支店', '2493-21': '三島支店',
                      '2493-22': '富士支店', '2493-23': '浜松支店', '2493-24': '掛川支店', '2493-27': '小牧支店', '2493-28': '岐阜支店',
                      '2493-29': '中部支店', '2493-30': '四日市支店',
                      '2493-31': '滋賀支店', '2493-33': '近江八幡支店', '2493-34': '京都支店', '2493-35': '大阪支店',
                      '2493-36': '南港支店', '2493-37': '貝塚支店', '2493-38': '奈良支店', '2493-39': '東大阪支店',
                      '2493-40': '松原支店', '2493-42': '和歌山支店', '2493-43': '淡路支店', '2493-44': '西神戸支店',
                      '2493-45': '三木小野支店', '2493-46': '加古川支店', '2493-47': '西脇支店', '2493-48': '福知山支店',
                      '2493-49': '姫路支店', '2493-50': '岡山支店', '2493-51': '福山支店', '2493-52': '広島支店', '2493-53': '徳山支店',
                      '2493-54': '山口支店', '2493-55': '高松支店', '2493-56': '新居浜支店', '2493-57': '松山支店',
                      '2493-58': '徳島支店', '2493-59': '丸亀支店', '2493-60': '福岡支店', '2493-61': '大牟田支店',
                      '2493-62': '中津支店', '2493-63': '北九州支店', '2493-100': 'トールエクスプレスジャパン　本社', '2493-108': '羽生支店',
                      '2493-111': '尼崎支店', '2493-112': '中九州支店', '2493-113': '長崎支店', '2493-114': '大分支店',
                      '2493-115': '熊本支店', '2493-116': '佐世保支店', '2493-117': '鹿児島支店', '2493-118': '佐賀支店',
                      '2493-119': '天草支店', '2493-120': '八代支店', '2493-121': '人吉支店', '2493-122': '宮崎支店',
                      '2493-123': '日向支店', '2493-124': '水俣支店', '2493-125': '姶良支店', '2493-126': '川内支店',
                      '2493-130': '安城支店', '2493-131': '名古屋支店', '2505-1': '千葉工場', '2505-2': '厚木工場', '2505-3': '浜松工場',
                      '2505-4': '中部工場', '2505-5': '四日市工場', '2505-6': '大阪工場', '2505-7': '東大阪工場', '2505-8': '西脇工場',
                      '2505-11': '福山工場', '2505-13': '高松工場', '2505-15': '福岡工場', '2505-17': '中九州工場',
                      '2505-18': '熊本工場', '2505-19': '八代工場', '2508-9': '長崎センター', '2508-18': '宮崎センター',
                      '2508-19': '栗野食品センター',
                      '2508-20': '熊本センター', '2508-22': '福岡センター', '2508-23': '九州産交運輸　本社', '2508-29': '鹿児島センター',
                      '2508-30': '佐賀事業所', '2508-32': '熊本コンテナセンター', '2508-33': '八代コンテナ事業所', '2508-34': '鹿児島センター',
                      '2508-35': '福岡コンテナ事業所',
                      '2508-36': '北九州コンテナ事業所', '2508-37': '中九州センター'}

    billing_data = []
    day_billing_data = []
    writer_data = []
    pass_data = []

    for row in data:
        unit_price = row[BILLING_UNIT_PRICE_NUM]
        if not unit_price:
            unit_price = ''
        else:
            unit_price = float(unit_price)

        amount = row[BILLING_AMOUNT_NUM]
        if not amount:
            amount = ''
        else:
            amount = float(amount)

        total = row[BILLING_TOTAL_NUM]
        if not total:
            total = ''

        else:
            total = int(total)

        store_code = row[BILLING_STORE_CODE_NUM]

        store_nam = row[BILLING_STORE_NAM_NUM]
        day = row[BILLING_DAY_NUM]
        # print(day)
        pt_code = int(row[BILLING_PT_CODE_NUM])
        pt_nam = row[BILLING_PT_NAM_NUM]
        item_nam = row[BILLING_ITEM_NAM_NUM]
        item_code = row[BILLING_ITEM_CODE_NUM]
        unit = row[BILLING_UNIT_NUM]
        remark = row[BILLING_REMARK_NUM]

        # トール以外の行をなるべく外す処理
        if (zenTOLL not in store_nam and zenTOLL not in item_nam and zenTOLL not in remark and \
            hanTOLL not in store_nam and hanTOLL not in item_nam and hanTOLL not in remark and \
            otherTOLL not in store_nam and otherTOLL not in item_nam and otherTOLL not in remark) and \
                ('2493' not in store_code and '2493' not in remark and \
                 '2505' not in store_code and '2505' not in remark and '2508' not in store_code and '2508' not in remark):
            if int(pt_code) not in [3370, 3443, 3381, 1023, 3761, 1100, 5172, 3350, 2857, 5145, 2877]:
                pass_data.append([store_code, store_nam, item_nam, remark, pt_code, pt_nam])
                continue

        # store_codeが無ければ(部門コード列空欄)、dictのkey(取引先コード-事業所コード)をいれる
        if not store_code:
            for key, value in all_store_code.items():
                # store_codeがない場合、store_nam/ramark/item_numに事業所名が一致するものがないか確認
                if (store_nam is not None and value in store_nam) or (remark is not None and value in remark) or (
                        item_nam is not None and value in item_nam):
                    store_code = str(key)
                    store_nam = value
                    break

        # store_codeはある前提。if not store_code:〜store_code = str(key)の間で条件一致していれば、store_codeは空にならない
        # dictに一致しないということは、そもそもトール関連の請求ではない可能性が高い
        if store_code:
            # print(store_code)
            if not store_nam:
                for key, value in all_store_code.items():
                    if store_code in key:
                        # store_code = str(key)  ←ここはここと同じことしてるかも？→if not store_code:〜store_code = str(key)
                        store_nam = value
                        break

            # else:
            # print(pt_code, store_nam)
            # 一度、store_namに値を探して入れてあげているにも関わらず、store_nameがない！！
            # この時の処理をどうする？？
            # print('if not store_nam:', store_code,store_nam, pt_code, pt_nam)

            # 既にstore_namはある前提！
            # if store_nam:
            # print('split(-で分割）前にstore_codeが文字化けしていないか？', store_code, store_nam, pt_code, pt_nam)

            store_split = store_code.split('-')
            customer_mach = re.search(r'(\d{4})', str(store_split[0]))
            # split後のstore_codeが文字化けしてたら、↓コードの実装を検討する
            # store_mach = re.search(r'(\d+)', str(store_split[1]))
            if not customer_mach:
                customer_code = store_split[0]
                store_code = int(store_split[1])
                # print('if not:', store_split[0], store_code)

            else:
                customer_code = store_split[0]
                store_code = int(store_split[1])
                # print('else customer_code, store_code:', customer_code, store_code)


        # この段階で、さらにstore_codeがなければ、どうやって処理を続けるか考える？
        # 更に、store_codeもstore_namもない行に対しての処理はココ！
        else:
            store_code = '未入力'
            customer_code = '未入力'

        # print('未入力store_code, store_nam, pt_code, pt_nam', store_code, store_nam, pt_code, pt_nam)

        if int(pt_code) == 3422:
            if 'プラ' in remark or 'ﾌﾟﾗ' in remark:
                item_nam = 'プラパレット'
            else:
                item_nam = '木パレット'
        elif int(pt_code) == 3742:
            if store_code == '未入力':
                customer_code = '2493'
                item_nam = '木パレット'
                if '若松' in row[8]:
                    store_code = '63'
                    store_nam = '北九州支店'
                else:
                    store_code = '34'
                    store_nam = '京都支店'

        billing_list = [store_code, pt_code, unit_price, amount, total]
        # billing_list: <class 'int'> <class 'int'> <class 'str'> <class 'str'> <class 'str'>
        # print('billing_list:',type(store_code), type(pt_code), type(unit_price), type(amount), type(total))
        billing_data.append(billing_list)

        all_billing_data = [customer_code, store_code, store_nam, day, pt_code, pt_nam, item_code, item_nam,
                            unit_price, amount, unit, total, remark]
        # all_billing_data = [store_code, store_nam, day, pt_code, pt_nam, item_code, item_nam, unit_price, amount, unit, total, remark]

        compare = [all_billing_data[1], all_billing_data[4], all_billing_data[8], all_billing_data[9],
                   all_billing_data[11]]
        # compare = [all_billing_data[0], all_billing_data[3], all_billing_data[7], all_billing_data[8],all_billing_data[10]]

        for b in brycen_data:
            # brycen_dataとbilling_listのstore_code、pt_code、unit_price、amount、totalが
            # 完全一致した行をbilling_dataからremove
            if billing_list == b:
                # print('mach:' billing_list)
                billing_data.remove(b)


            # brycen_dataとbilling_listのstore_code、pt_code、totalが
            # 完全一致した行をbilling_dataからremove
            # elif [billing_list[STORE_CODE_LIST_INDEX], billing_list[PT_CODE_LIST_INDEX],
                  # billing_list[TOTAL_LIST_INDEX]] == [b[BRYCEN_STORE_CODE_LIST_INDEX], b[BRYCEN_PT_CODE_LIST_INDEX],
                                                      # b[BRYCEN_TOTAL_LIST_INDEX]]:
                # billing_data.remove(billing_list)

        # brycen_dataとbilling_dataが不一致だった場合のみ
        # writer_dataにappend
        if compare in billing_data:
            writer_data.append(all_billing_data)



    # ディレクトリ命名
    now = datetime.now()
    today = now.strftime('%Y/%m%d/')
    media_dir = settings.MEDIA_URL # media_dir: /media/

    dir_name = os.path.join(os.getcwd(), 'media', 'matched_data_file', today)
    print('dir_name:{}'.format(dir_name))

    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    # ファイル命名
    # file_name = 'TXJ_付け合わせ済' + '(' + now.strftime('%Y年%m月%d日%H時%M分%S秒') + '_作成分)' + '.csv'
    file_name = 'TXJ_付け合わせ済'+ now.strftime('%Y年%m月%d日%H時%M分%S秒') + '_作成分' + '.csv'
    download_filename = {'download_filename': file_name}
    # print('filename1: {}'.format(file_name), )

    file_path = os.path.join(dir_name, file_name)
    # print('file_path: {} '.format(file_path))


    # output_file = open(file_name, 'w', newline='')
    with open(file_path, 'w', newline='') as output_file:
        output_writer = csv.writer(output_file)
        output_writer.writerow(
            ['取引先名', '支店番号', '支店名', '日付', '業者番号', '業者名', '商品コード', '品目', '単価', '数量', '単位', '合計金額', '備考'])
        output_writer.writerows(writer_data)
    # print('filename2:{}'.format(file_name))

    # TXJ以外の請求行（突合済ファイルに反映されない請求データ）をprintする。
    # for pass_item in pass_data:
        # print(
        #'============= Pass \n store: {} {} \n item_remark : {}_{} \n pt    :{} {} ============'.format(
        # pass_item[0], pass_item[1], pass_item[2], pass_item[3], pass_item[4], pass_item[5]))

    return file_path


class MatchedDataDetailView(DetailView):
    model = MatchedData
    template_name = 'app/matched_data_detail.html'

    def get_context_data(self, **kwargs):
        matched_data_pk = self.kwargs['pk']
        matched = MatchedData.objects.get(pk=matched_data_pk)

        brycen_file_path = urllib.parse.unquote(matched.brycen_file.url)
        brycen_file_path_split = os.path.split(brycen_file_path)
        brycen_file_name = brycen_file_path_split[1]

        billing_file_path = urllib.parse.unquote(matched.billing_file.url)
        billing_file_path_split = os.path.split(billing_file_path)
        billing_file_name = billing_file_path_split[1]

        context = super().get_context_data(**kwargs)
        context['matched'] = matched
        context['brycen_file_name'] = brycen_file_name
        context['billing_file_name'] = billing_file_name
        context['matched_file'] = urllib.parse.unquote(matched.matched_data_file.url)
        context['status'] = CSV_OUTPUT_COMPLETED

        return context


class VisuallyMatchedDataCreateView(CreateView):
    model = VisuallyMatchedData
    form_class = VisuallyMatchedDataCreateForm
    template_name = 'app/visually_match.html'

    def get_context_data(self, **kwargs):
        matched_data_pk = self.kwargs['pk']
        matched = MatchedData.objects.get(pk=matched_data_pk)
        matched_file_path = urllib.parse.unquote(matched.matched_data_file.url)
        matched_file_path_split = os.path.split(matched_file_path)
        matched_file_name = matched_file_path_split[1]
        context = super().get_context_data(**kwargs)
        context['status'] = CSV_OUTPUT_COMPLETED
        context['matched'] = matched
        context['matched_data_file_name'] = matched_file_name

        return context

    def form_valid(self, form):
        visually_matched = form.save(commit=False)
        author = Staff.objects.get(author=self.request.user)
        visually_matched.author = author
        matched_data_pk = self.kwargs['pk']
        matched = MatchedData.objects.get(pk=matched_data_pk)
        visually_matched.matched_id = matched.id
        visually_matched.save()

        generated_data_pk = visually_matched.matched.generated.pk
        generated = GeneratedData.objects.get(pk=generated_data_pk)
        generated.status = GeneratedData.VISUALLY_CONFIRMED
        generated.save()

        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        return reverse('import_data', kwargs={'pk': self.object.pk})


class ImportDataCreateView(CreateView):
    model = ImportData
    form_class = ImportDataCreateForm
    template_name = 'app/import_data.html'

    def get_context_data(self, **kwargs):
        visually_matched_data_pk = self.kwargs['pk']
        visually_matched = VisuallyMatchedData.objects.get(pk=visually_matched_data_pk)

        matched_data_pk = visually_matched.matched_id
        matched = MatchedData.objects.get(pk=matched_data_pk)
        matched_data_file = urllib.parse.unquote(matched.matched_data_file.url)
        matched_data_file_path_split = os.path.split(matched_data_file)
        matched_data_file_name = matched_data_file_path_split[1]

        context = super().get_context_data(**kwargs)
        context['matched_data_file_name'] = matched_data_file_name
        context['matched_data_file'] = matched_data_file
        context['visually_matched'] = visually_matched
        context['status'] = VISUALLY_CONFIRMED
        return context

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        if self.request.method == 'POST':
            if 'upload_and_create' in self.request.POST:
                form_kwargs.update({'upload_and_create': self.request.POST.get('upload_and_create', None) is not None})
            elif 'create' in self.request.POST:
                form_kwargs.update({'create': self.request.POST.get('create', None) is not None})
        return form_kwargs

    def form_valid(self, form):
        if 'upload_and_create' in self.request.POST:
            import_data = form.save(commit=False)
            author = Staff.objects.get(author=self.request.user)
            import_data.author = author
            visually_matched_data_pk = self.kwargs['pk']
            visually_matched = VisuallyMatchedData.objects.get(pk=visually_matched_data_pk)
            import_data.visually_matched_id = visually_matched.id
            import_data.save()

            if import_data.visually_matched_file:
                visually_matched_file_path = urllib.parse.unquote(import_data.visually_matched_file.path)
                file_path = import_data_create(visually_matched_file_path)

        elif 'create' in self.request.POST:
            import_data = form.save(commit=False)
            author = Staff.objects.get(author=self.request.user)
            import_data.author = author
            visually_matched_data_pk = self.kwargs['pk']
            visually_matched = VisuallyMatchedData.objects.get(pk=visually_matched_data_pk)
            import_data.visually_matched_id = visually_matched.id
            matched_file_path = urllib.parse.unquote(visually_matched.matched.matched_data_file.path)
            file_path = import_data_create(matched_file_path)
            import_data.save()



        generated_data_pk = import_data.visually_matched.matched.generated.pk
        # print('generated_data_pk:{}'.format(generated_data_pk))
        generated = GeneratedData.objects.get(pk=generated_data_pk)
        generated.status = GeneratedData.IMPORT_DATA_OUTPUT_COMPLETED
        generated.save()

        # create_import_dataのfile_pathを取得し、file_pathからImportDataのimport_data_fileフィールドに紐付け
        path_split = os.path.split(file_path)
        dir_name = path_split[0]
        file_name = path_split[1]
        dir_name_split = dir_name.split('/')
        # /Users/name/PycharmProjects/Tool/media/matched_data_file/2020/1008/の/media/以降がdir_name_list
        dir_name_list = dir_name_split[6:]
        import_data_file_dir = '/'.join(dir_name_list)
        import_data_file_path = os.path.join(import_data_file_dir, file_name)
        import_data.import_data_file = import_data_file_path
        # print('import_data_file:{}'.format(import_data.import_data_file))

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('import_data_detail', kwargs={'pk': self.object.pk})


# インポートデータ作成ロジック
def import_data_create(f):
    STORE_CODE_LIST_INDEX = 0
    DAY_LIST_INDEX = 1
    PT_CODE_LIST_INDEX = 2
    UNIT_PRICE_LIST_INDEX = 3
    AMOUNT_LIST_INDEX = 4
    UNIT_LIST_INDEX = 5
    TOTAL_LIST_INDEX = 6
    REMARK_LIST_INDEX = 7
    PRODUCT_CODE_LIST_INDEX = 8
    PRODUCT_NAM_LIST_INDEX = 9
    ITEM_CODE_LIST_INDEX = 10
    UNIT_CODE_LIST_INDEX = 11

    STORE_CODE_COL_NUM = 1
    DAY_COL_NUM = 3
    PT_CODE_COL_NUM = 4
    PRODUCT_COL_NUM = 6
    ITEM_COL_NUM = 7
    UNIT_PRICE_COL_NUM = 8
    AMOUNT_COL_NUM = 9
    UNIT_COL_NUM = 10
    TOTAL_COL_NUM = 11

    # 単位がtできた請求データをkgに変換する関数
    def kg_conversion():
        kg = int(amount * 1000)
        l[AMOUNT_LIST_INDEX] = kg

        kg_unit_price = int(total / kg)
        l[UNIT_PRICE_LIST_INDEX] = kg_unit_price

        l[UNIT_LIST_INDEX] = 'kg'
        l[UNIT_CODE_LIST_INDEX] = '0'

    # 数量を備考欄に反映させ、数量を1式に変換する関数
    def kg_remake():
        l[UNIT_PRICE_LIST_INDEX] = total
        l[AMOUNT_LIST_INDEX] = 1
        l[REMARK_LIST_INDEX] = str(unit_price) + '円' + '×' + '{:,}'.format(int(amount)) + 'kg'
        l[UNIT_CODE_LIST_INDEX] = '2'

    file = open(f)  # csvファイルを読み込んだ内容をfileに入れる
    reader = csv.reader(file)  # csvファイルを開いて、開いた内容をreaderに入れる　
    data = list(reader)  # 開いた内容をリストで取得して、dataに入れる
    # last_row = sum(1 for i in open(f))  # CSVファイルの最終行を取得

    #  pt_codeが10101の単価15だった場合の行数を取得
    n_row_count = 1
    for n in data:
        if n[PT_CODE_COL_NUM] == '10101' and n[UNIT_PRICE_COL_NUM] == '15':
            n_row_count += 1

    # write_max_row = last_row - n_row_count  # csv最終行数 - pt_code 10101の単価15だった場合の行数　= Excelに書き出される行数値 ex. 130 - 5 = 125

    wb = openpyxl.load_workbook('/Users/ishiwata/PycharmProjects/Tool/media/import_data_format_file/import_data_format.xlsx')
    ws = wb.active
    # max_row = ws.max_row + 1
    # ws.delete_rows(idx=write_max_row + n_row_count, amount=max_row - last_row)  # idx= 何行目から　amount= 何行分削除するか
    # print('max',max - 1,'amount',max - last_row,'indx',write_max_row + n_row_count)

    current_dir = os.getcwd()

    # csvファイルの1行目（項目）を削除
    data.remove(data[0])

    i = 6  # 実際にExcelへ書き出す行数（6行目から書き出し開始）
    row_count = 0  # Excelに書き出された行数をカウント

    # csvから必要な値を取得
    for row in data:
        store_code = row[STORE_CODE_COL_NUM]
        if store_code == '未入力':
            continue
        store_code = str(store_code.rjust(5, '0'))

        # print(row[DAY_COL_NUM])
        match = re.search(r'(\d{4})/(\d+)/(\d+)', str(row[DAY_COL_NUM]))
        year = int(match.group(1))
        month = int(match.group(2))
        date = int(match.group(3))
        conv_date = datetime(year, month, date) - datetime(1899, 12, 30)
        day = int(conv_date.days)

        # day = dt.strptime(row[DAY_COL_NUM], '%Y-%m-%d %H:%M:%S')  # %Y-%m-%d %H:%M:%S
        pt_code = str(row[PT_CODE_COL_NUM].rjust(5, '0'))

        amount = row[AMOUNT_COL_NUM]
        if amount:
            amount = float(amount)

        unit = row[UNIT_COL_NUM]

        total = int(row[TOTAL_COL_NUM])

        product_code = row[PRODUCT_COL_NUM]
        if product_code:
            product_code = int(product_code)

        item = row[ITEM_COL_NUM]

        product_name = None
        item_code = None

        # PT：10101の単価15.0の行はlに入れない
        if pt_code == '10101':
            if day == day:
                if int(float(row[UNIT_PRICE_COL_NUM])) == 15:
                    continue

        # 単価はfloatで取得
        if row[UNIT_PRICE_COL_NUM]:
            unit_price = float(row[UNIT_PRICE_COL_NUM])

        # 単価の入力が無かったら、空文字のまま取得
        else:
            if not row[UNIT_PRICE_COL_NUM]:
                unit_price = ''

        # TODO:商品コードを判定し、商品名、商品コード、品目コードを設定する
        if product_code == 4:
            product_code = '0004'
            product_name = '産廃税'
            item_code = '17'

        elif product_code == 110:
            product_code = '0110'
            product_name = '機密文書処理'
            # item_code = '対象コードがありません：品目を確認してください'
            item_code = ''

        elif product_code == 202:
            product_code = '0202'
            product_name = 'マニフェスト伝票代'
            item_code = '11'

        elif product_code == 404:
            product_code = '0404'
            product_name = 'コンテナレンタル費用'
            item_code = '2'

        # product_codeが5103の場合のみitem（品目列）が、
        # コンテナ交換or産業廃棄物かで、item_codeが異なる
        # ただし、上記item以外の場合は全て産業廃棄物のitem_codeになる
        elif product_code == 5103:
            product_code = '5103'
            product_name = '産業廃棄物収集運搬処分費'

            if item == 'コンテナ交換':
                item_code = '1'

            elif item == '産業廃棄物':
                item_code = '10'

            else:
                item_code = '10'

        elif product_code == 5105:
            product_code = '5105'
            product_name = '産業廃棄物（木パレット）収集運搬処分費'
            item_code = '0'

        elif product_code == 5106:
            product_code = '5106'
            product_name = '産業廃棄物（プラパレット）収集運搬処分費'
            item_code = '10'

        elif product_code == 5107:
            product_code = '5107'
            product_name = '産業廃棄物（ストレッチフィルム）収集運搬処分費'
            item_code = '3'

        elif product_code == 9004 and unit_price <= 0:
            product_code = '9004'
            product_name = '産業廃棄物（スポット スクラップ類）収集運搬処分費（買取）'
            item_code = '7'

        elif product_code == 9008 and unit_price <= 0:
            product_code = '9008'
            product_name = 'リサイクル物運搬費（買取）'
            item_code = '18'

        elif product_code == 9012 and unit_price <= 0:
            product_code = '9012'
            product_name = '資源（ストレッチフィルム）収集運搬処分費（買取）'
            item_code = '3'

        elif product_code == 9013 and unit_price <= 0:
            product_code = '9013'
            product_name = '資源（廃油）収集運搬処分費（買取）'
            item_code = '16'

        elif product_code == 9014 and unit_price <= 0:
            product_code = '9014'
            product_name = '資源（台タイヤ）収集運搬処分費（買取）'
            item_code = '14'

        elif product_code == 9015 and unit_price <= 0:
            product_code = '9015'
            product_name = '廃油収集運搬処分費（買取）'
            item_code = '16'

        elif product_code == 9016 and unit_price <= 0:
            product_code = '9016'
            product_name = '資源物収集運搬処分費（買取）'
            # item_code = '対象コードがありません：品目を確認してください'
            item_code = ''

        else:
            pass
            # print(product_code)

            # TODO:明細項目を判定し、商品名、商品コード、品目コードを設定する
            if item == '産廃税':
                product_code = '0004'
                product_name = '産廃税'
                item_code = '17'

            elif item == '機密文書':
                product_code = '0110'
                product_name = '機密文書処理'
                # item_code = '対象コードがありません：品目を確認してください'
                item_code = ''

            elif item == 'マニフェスト':
                product_code = '0202'
                product_name = 'マニフェスト伝票代'
                item_code = '2'

            elif item == 'コンテナ交換':
                product_code = '5103'
                product_name = '産業廃棄物収集運搬処分費'
                item_code = '1'

            elif item == '産業廃棄物':
                product_code = '5103'
                product_name = '産業廃棄物収集運搬処分費'
                item_code = '10'

            elif item == '木パレット':
                product_code = '5105'
                product_name = '産業廃棄物（木パレット）収集運搬処分費'
                item_code = '0'

            elif item == 'プラパレット':
                product_code = '5106'
                product_name = '産業廃棄物（プラパレット）収集運搬処分費'
                item_code = '10'

            elif item == 'ストレッチフィルム':
                product_code = '5107'
                product_name = '産業廃棄物（ストレッチフィルム）収集運搬処分費'
                item_code = '3'

            elif item == 'スクラップ類　買取' and unit_price <= 0:
                product_code = '9004'
                product_name = '産業廃棄物（スポット スクラップ類）収集運搬処分費（買取）'
                item_code = '7'

            elif item == '廃バッテリー　買取' and unit_price <= 0:
                product_code = '9008'
                product_name = 'リサイクル物運搬費（買取）'
                item_code = '18'


            elif item == 'ストレッチフィルム　買取' and unit_price <= 0:
                product_code = '9012'
                product_name = '資源（ストレッチフィルム）収集運搬処分費（買取）'
                item_code = '3'


            elif item == '廃油　買取' and unit_price <= 0:
                product_code = '9013'
                product_name = '資源（廃油）収集運搬処分費（買取）'
                item_code = '16'


            elif item == '台タイヤ　買取' and unit_price <= 0:
                product_code = '9014'
                product_name = '資源（台タイヤ）収集運搬処分費（買取）'
                item_code = '14'


            elif item == '廃油　買取' and unit_price <= 0:
                product_code = '9015'
                product_name = '廃油収集運搬処分費（買取）'
                item_code = '16'


            elif item == '資源物　買取' and unit_price <= 0:
                product_code = '9016'
                product_name = '資源物収集運搬処分費（買取）'
                # item_code = '対象コードがありません：品目を確認してください'
                item_code = ''

            else:
                pass
                # print(item)

        # TODO:単位列を判定し、請求書記載単位コードを設定する
        if unit == 'ｋｇ':
            unit_code = '0'

        elif unit == 'Ｋｇ':
            unit_code = '0'

        elif unit == 'kg':
            unit_code = '0'

        elif unit == 'Kg':
            unit_code = '0'

        elif unit == '㎏':
            unit_code = '0'

        elif unit == '車':
            unit_code = '1'

        elif unit == '式':
            unit_code = '2'

        elif unit == '立法メートル':
            unit_code = '4'

        elif unit == '立米':
            unit_code = '4'

        elif unit == 'm3':
            unit_code = '4'

        elif unit == '回':
            unit_code = '5'

        elif unit == '台':
            unit_code = '7'

        elif unit == '枚':
            unit_code = '10'

        else:
            # unit_code = '単位を確認してください'
            unit_code = ''

        l = [store_code, day, pt_code, unit_price, amount, unit, total, '', product_code, product_name, item_code,
             unit_code]

        # TODO:イレギュラーPTを判定　→　特殊計算ロジック
        if pt_code == '03422':
            if unit_price == 14.5:
                kg_remake()

            elif unit_price == 4.5:
                kg_remake()

            elif unit_price == 12:
                l[UNIT_PRICE_LIST_INDEX] = total
                l[AMOUNT_LIST_INDEX] = 1
                l[REMARK_LIST_INDEX] = str(int(unit_price)) + '円' + '×' + '{:,}'.format(int(amount)) + 'kg'
                l[UNIT_CODE_LIST_INDEX] = '2'

            elif unit_price == 2:
                l[UNIT_PRICE_LIST_INDEX] = total
                l[AMOUNT_LIST_INDEX] = 1
                l[REMARK_LIST_INDEX] = str(int(unit_price)) + '円' + '×' + '{:,}'.format(int(amount)) + 'kg'
                l[UNIT_CODE_LIST_INDEX] = '2'

            else:
                l[UNIT_PRICE_LIST_INDEX] = int(unit_price)
                l[AMOUNT_LIST_INDEX] = int(amount)

        elif pt_code == '10101':
            l[UNIT_PRICE_LIST_INDEX] = int(unit_price) + 15.0
            l[AMOUNT_LIST_INDEX] = int(amount)
            l[TOTAL_LIST_INDEX] = int(amount) * int(unit_price)
            l[UNIT_CODE_LIST_INDEX] = '0'

        elif pt_code == '03365':
            if unit_price == 7.7:
                kg_remake()

        elif pt_code == '03761':
            if unit_price == 1500:
                l[UNIT_PRICE_LIST_INDEX] = total
                l[AMOUNT_LIST_INDEX] = 1
                l[REMARK_LIST_INDEX] = '{:,}'.format(int(unit_price)) + '円' + '×' + str(amount) + '立米'
                l[UNIT_CODE_LIST_INDEX] = '2'

            else:
                l[UNIT_PRICE_LIST_INDEX] = int(unit_price)
                l[AMOUNT_LIST_INDEX] = int(amount)
                l[UNIT_CODE_LIST_INDEX] = 2

        #  単位がt(半角）だった場合
        elif unit == 't':
            kg_conversion()

        #  単位がt(全角）だった場合
        elif unit == 'ｔ':
            kg_conversion()

        #  単価が空で尚且つ、数量も空だった場合
        elif unit_price == '':
            if not amount:
                l[UNIT_PRICE_LIST_INDEX] = total
                l[AMOUNT_LIST_INDEX] = 1
                l[UNIT_CODE_LIST_INDEX] = 2

            elif int(amount) == 1:
                l[UNIT_PRICE_LIST_INDEX] = total
                l[AMOUNT_LIST_INDEX] = 1
                l[REMARK_LIST_INDEX] = str(amount) + str(unit)
                # l[UNIT_CODE_LIST_INDEX] = '単位を確認してください'
                l[UNIT_CODE_LIST_INDEX] = '2'

            else:
                l[UNIT_PRICE_LIST_INDEX] = total
                l[AMOUNT_LIST_INDEX] = 1
                l[REMARK_LIST_INDEX] = str(amount) + str(unit)


        ws.cell(column=1, row=i).value = l[STORE_CODE_LIST_INDEX]
        ws.cell(column=55, row=i).value = l[DAY_LIST_INDEX]
        ws.cell(column=68, row=i).value = l[PT_CODE_LIST_INDEX]
        ws.cell(column=77, row=i).value = l[UNIT_PRICE_LIST_INDEX]
        ws.cell(column=78, row=i).value = l[AMOUNT_LIST_INDEX]
        ws.cell(column=74, row=i).value = l[REMARK_LIST_INDEX]
        ws.cell(column=75, row=i).value = l[PRODUCT_CODE_LIST_INDEX]
        ws.cell(column=80, row=i).value = l[PRODUCT_NAM_LIST_INDEX]
        ws.cell(column=82, row=i).value = l[ITEM_CODE_LIST_INDEX]
        ws.cell(column=83, row=i).value = l[UNIT_CODE_LIST_INDEX]
        ws.cell(column=54, row=i).value = 2  # 契約タイプ区分

        emission_column = ['B', 'M', 'X', 'AI']
        zero_column = ['C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'Y', 'Z',
                       'AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AJ', 'AK', 'AL', 'AM', 'AN', 'AO', 'AP', 'AQ', 'AU',
                       'AV', 'AW', 'AZ', 'CA']
        one_column = ['BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BK', 'BL', 'BM', 'BN', 'BO', 'BX']

        for c in emission_column:
            column = openpyxl.utils.column_index_from_string(c)  # 列を数値に変換
            ws.cell(row=i, column=column).value = 0.00

        for c in zero_column:
            column = openpyxl.utils.column_index_from_string(c)
            ws.cell(row=i, column=column).value = 0

        for c in one_column:
            column = openpyxl.utils.column_index_from_string(c)
            ws.cell(row=i, column=column).value = 1

        i += 1
        row_count += 1

    max_row = ws.max_row + 1
    # import_data_formatの6行目以降の不要行を削除
    ws.delete_rows(idx=row_count + 6, amount=max_row - (row_count + 6))  # idx= 何行目から　amount= 何行分削除するか

    # ディレクトリ命名
    now = datetime.now()
    today = now.strftime('%Y/%m%d/')
    media_dir = settings.MEDIA_URL # media_dir: /media/

    dir_name = os.path.join(os.getcwd(), 'media', 'import_data_file', today)
    # print('dir_name:{}'.format(dir_name))

    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    # ファイル命名
    file_name = 'TXJ_import_data'+ now.strftime('%Y年%m月%d日%H時%M分%S秒') + '_作成分' + '.xlsx'
    # print('filename1: {}'.format(file_name), )

    file_path = os.path.join(dir_name, file_name)
    # print('file_path: {} '.format(file_path))

    wb.save(file_path)
    return file_path


class ImportDataDetailView(DetailView):
    model = ImportData
    template_name = 'app/import_data_detail.html'

    def get_context_data(self, **kwargs):
        import_data_pk = self.kwargs['pk']
        import_data = ImportData.objects.get(pk=import_data_pk)

        matched_data_pk = import_data.visually_matched.matched.pk
        matched_data = MatchedData.objects.get(pk=matched_data_pk)
        matched_data_file_path = urllib.parse.unquote(matched_data.matched_data_file.url)
        matched_data_file_path_split = os.path.split(matched_data_file_path)
        matched_data_file_name = matched_data_file_path_split[1]

        brycen_file_path = urllib.parse.unquote(matched_data.brycen_file.url)
        brycen_file_path_split = os.path.split(brycen_file_path)
        brycen_file_name = brycen_file_path_split[1]

        billing_file_path = urllib.parse.unquote(matched_data.billing_file.url)
        billing_file_path_split = os.path.split(billing_file_path)
        billing_file_name = billing_file_path_split[1]

        context = super().get_context_data(**kwargs)

        if import_data.visually_matched_file:
            visually_matched_file_path = urllib.parse.unquote(import_data.visually_matched_file.url)
            visually_matched_file_path_split = os.path.split(visually_matched_file_path)
            visually_matched_file_name = visually_matched_file_path_split[1]
            context['visually_matched_file_name'] = visually_matched_file_name

        context['import_data'] = import_data
        context['import_data_file'] = urllib.parse.unquote(import_data.import_data_file.url)
        context['matched_data'] = matched_data
        context['matched_data_file_name'] = matched_data_file_name
        context['brycen_file_name'] = brycen_file_name
        context['billing_file_name'] = billing_file_name
        context['status'] = IMPORT_DATA_OUTPUT_COMPLETED
        return context





