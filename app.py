import functools
from pathlib import Path

from api import Goods, Inventory, test_tokens
import streamlit as st
from st_aggrid import AgGrid
from st_aggrid import DataReturnMode, GridUpdateMode
from st_aggrid.shared import JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import pandas as pd
from pyecharts.charts import Bar, Pie
from pyecharts import options as opts
from pyecharts.globals import ThemeType
import streamlit_echarts
import json



def delete_goods(inventory, index):
    for i in index:
        inventory.delete(i['库存编号'])


def sell_goods(inventory, index):
    for i in index:
        try:
            inventory()[i['库存编号']].sell(eval(i['卖出价格']))
        except:
            st.error("卖出价格输入错误，请检查输入")

def lease_goods(inventory, index):
    for i in index:
        inventory()[i['库存编号']].lease()


def back_goods(inventory, index):
    for i in index:
        inventory()[i['库存编号']].back()



def open_inventory(path):
    if type(path) == str:
        st.session_state.inventory=Inventory(path)
        st.session_state.inventory.save()
    else:
        with st.spinner("加载库存中..."):
            st.session_state.inventory = Inventory(path.name)
            st.success("库存已打开 ✅")
        with open(st.session_state.inventory.path,'wb+') as file:
            file.write(path.getvalue())
    with st.spinner("更新饰品信息..."):
        progress_bar = st.progress(0)
        if len(st.session_state.inventory())<=0:
            rate=1
        else:
            rate = 1 / len(st.session_state.inventory())
        for p, i in enumerate(st.session_state.inventory):
            progress_bar.progress(rate * p)
            st.session_state.inventory()[i].refresh()
        progress_bar.empty()


def save_inventory(path):
    with st.spinner("保存库存中..."):
        st.session_state.inventory.save()
        st.success("库存保存成功 ✅")
    with st.sidebar:
        with open(st.session_state.inventory.path, 'rb') as f:
            st.download_button('下载到本地', f, file_name=st.session_state.inventory.path)
def update_token(token):
    if not test_tokens(token):
        st.error("Token无效，请重新登陆悠悠，按F12查找token，格式为 Bearer xxx")
        return
    USER_TOKEN=token
    if 'inventory' in st.session_state:
        for good in st.session_state.inventory():
                st.session_state.inventory()[good].token=USER_TOKEN
    st.success("Token更新成功,请及时保存！！✅")
    
    
    
cellsytle_jscode = JsCode(
    """
function (params) {
        if (params.value < 0) {
            return {
                'color': 'white',
                'backgroundColor': 'forestgreen'
            }
        } else {
            return {
                'color': 'white',
                'backgroundColor': 'crimson'
            }
        } 
    };
    """
)

def import_from_file(path,token):
    if not "inventory" in st.session_state:
        st.error("请新建仓库在导入数据")
        return
    if not test_tokens(token):
        st.error("悠悠token不正确")
        return
    try:
        if path.name.endswith('.csv'):
            data=pd.read_csv(path.getvalue())
        elif path.name.endswith('.xlsx'):
            data=pd.read_excel(path.getvalue())
        else:
             st.error('%s 文件类型不支持'%path.name)
             return
        for i in range(data.shape[0]):
            tmp = Goods(str(data.iloc[i]['Buff id']), int(data.iloc[i]['购入花费(元)']),token=token)
            tmp.refresh()
            st.session_state.inventory.add(tmp)
            st.success(tmp.name + "已添加 ✅")
    except:
        st.error('检查%s中是否包含 <Buff id> <购入花费(元)>字段'%path)

def main() -> None:
    global USER_TOKEN
    st.header("CSGO 饰品投资追踪 :moneybag: :dollar: :bar_chart:")
    st.caption("Made by Shevon & Lishuai, maintained by whatcoldwind")
    st.text("请在左侧打开库存文件")
    with st.sidebar:
        st.subheader("选择库存")
        path = st.file_uploader("上传本地库存文件")
        if path:
            launch = st.button('打开库存', on_click=open_inventory, args=(path,))
        new_name=st.text_input("输入新建库存的名称",value="xxxxx")
        if new_name:
            new_one = st.button('新建库存', on_click=open_inventory, args=(new_name+'.pkl',))
        save = st.button('保存库存更改', on_click=save_inventory, args=(path,))
        token_value = st.text_input("token值", value=USER_TOKEN)
        token = st.button('更新悠悠有品token', on_click=update_token, args=(token_value,))
        
        if 'inventory' in st.session_state:
            import_file_path = st.file_uploader("上传导出表格文件并导入到当前仓库 *.csv *.xlsx")
            if import_file_path:
                import_bt = st.button('导入', on_click=import_from_file, args=(import_file_path,USER_TOKEN))
            st.caption('目前已启动库存 ' + st.session_state.inventory.path)
            st.subheader("添加饰品")
            form_track = st.form(key="track")
            with form_track:
                code = st.text_input("请输入饰品buff代码")
                cost = eval(st.text_input("请输入购买价格，0表示仅观望", "0"))
                submitted = st.form_submit_button(label="添加")
            if submitted:
                with st.spinner("加载饰品信息..."):
                    try:
                        tmp = Goods(code, cost,token=USER_TOKEN)
                        tmp.refresh()
                        st.session_state.inventory.add(tmp)
                        st.success(tmp.name + "已添加 ✅")
                    except:
                        st.error("饰品信息加载失败，请检查代码和token是否正确")

    if 'inventory' in st.session_state:
        for good in st.session_state.inventory():
            validation=test_tokens(st.session_state.inventory()[good].token)
            if validation :
                USER_TOKEN=st.session_state.inventory()[good].token
                st.success("✅ 你当前token有效：%s"%USER_TOKEN)
                break
        st.subheader("投资信息")
        if len(st.session_state.inventory()) > 0:
            col = st.columns(4)
            col2 = st.columns(4)
            col3 = st.columns(4)
            col[0].metric(
                "总投资额", value=f"{st.session_state.inventory.total_cost():.2f} 元",
                help="购买饰品总花费"
            )
            col[1].metric("追踪总量", value=f"{len(st.session_state.inventory())} 件",help="加入库存文件的饰品数量")
            col[2].metric(
                "库存价值(Buff计,含租出)",
                value=f"{st.session_state.inventory.calc_price():.2f} 元",
                help="库存饰品和已租出饰品总价值"
            )
            col[3].metric(
                "总套现", value=f"{st.session_state.inventory.sell_price():.2f} 元",
                help="卖出饰品总收入"
            )
            earn = (
                st.session_state.inventory.calc_price()
                + st.session_state.inventory.sell_price()
                - st.session_state.inventory.total_cost()
            )
            col2[0].metric("盈利(Buff计)", value=f"{earn:.2f} 元",
                           help="总套现 + 库存价值 - 总投资额")
            col2[1].metric(
                "总收益率",
                value=f"{earn/st.session_state.inventory.total_cost()*100:.2f} %",
                help="盈利 / 总投资额 * 100"            
            )
            yyyp_earn = (
                st.session_state.inventory.calc_yyyp_price()
                + st.session_state.inventory.sell_price()
                - st.session_state.inventory.total_cost()
            )
            col2[2].metric("盈利(悠悠有品计)", value=f"{yyyp_earn:.2f} 元")
            col2[3].metric(
                "总收益率",
                value=f"{yyyp_earn/st.session_state.inventory.total_cost()*100:.2f} %",
                help="盈利 / 总投资额 * 100"
            )
            col3[0].metric(
                "持有饰品收益(Buff计)",
                value=f"{st.session_state.inventory.calc_price() - st.session_state.inventory.total_cost_in_inventory():.2f} 元",
                help="库存价值 - 库存内和已租出饰品总花费"
            )
            col3[1].metric(
                "持有饰品收益率(Buff计)",
                value=f"{100 * (st.session_state.inventory.calc_price() - st.session_state.inventory.total_cost_in_inventory())/st.session_state.inventory.total_cost_in_inventory():.2f} %",
                help="( 持有饰品收益 - 库存内和已租出饰品总花费 ) * 100"
            )
            col3[2].metric(
                "持有饰品收益(悠悠有品计)",
                value=f"{st.session_state.inventory.calc_yyyp_price() - st.session_state.inventory.total_cost_in_inventory():.2f} 元",
                help="库存价值 - 库存内和已租出饰品总花费"
            )
            col3[3].metric(
                "持有饰品收益率(悠悠有品计)",
                value=f"{100 * (st.session_state.inventory.calc_yyyp_price() - st.session_state.inventory.total_cost_in_inventory())/st.session_state.inventory.total_cost_in_inventory():.2f} %",
                help="( 持有饰品收益 - 库存内和已租出饰品总花费 ) * 100"
            )
            st.subheader("目前资金组成")
            col4 = st.columns(2)
            with col4[0]:
                fig1 = Pie(init_opts=opts.InitOpts(theme=ThemeType.MACARONS)).add(
                    "库存资金组成",
                    [('出租',sum(
                            [
                                st.session_state.inventory()[good].price
                                for good in st.session_state.inventory()
                                if st.session_state.inventory()[good].status == 1
                            ]
                        )), 
                     ('在库',sum(
                            [
                                st.session_state.inventory()[good].price
                                for good in st.session_state.inventory()
                                if (
                                    st.session_state.inventory()[good].status == 0
                                    and st.session_state.inventory()[good].cost != 0
                                )
                            ]
                        ))],
                    radius=["30%", "75%"],
                )
                streamlit_echarts.st_pyecharts(fig1, height="400px", key="fig1")
            with col4[1]:
                fig2 = Pie(init_opts=opts.InitOpts(theme=ThemeType.MACARONS)).add(
                    "盈利资金组成",
                    [('库存增值',st.session_state.inventory.calc_price()
                        - st.session_state.inventory.total_cost_in_inventory(),), ('卖出收益',st.session_state.inventory.sell_earn(),)],
                    radius=["30%", "75%"],
                )
                streamlit_echarts.st_pyecharts(fig2, height="400px", key="fig2")
        else:
            st.caption("当前库存为空")
        # 追踪列表
        st.subheader("追踪列表")
        st.text("右键表格可以导出表格")
        if len(st.session_state.inventory()) > 0:
            data = pd.DataFrame(
                columns=['库存编号', 'Buff id', '名称', '状态', '购入花费(元)', '卖出价格']
            )
            for xx in st.session_state.inventory:
                xx = st.session_state.inventory()[xx]
                data.loc[len(data)] = [
                    xx.index,
                    xx.id,
                    xx.name,
                    xx.get_status(),
                    xx.cost,
                    xx.sell_price,
                ]

            gb = GridOptionsBuilder.from_dataframe(data)

            gb.configure_selection(
                selection_mode='multiple',
                use_checkbox=True,
            )
            gb.configure_side_bar()
            gb.configure_grid_options(domLayout='normal')
            gridOptions = gb.build()
            grid = AgGrid(
                data,
                gridOptions=gridOptions,
                allow_unsafe_jscode=True,
                return_mode_value=DataReturnMode.FILTERED,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                enable_enterprise_modules=True,
            )
            selected = grid["selected_rows"]
            if selected != []:
                print(selected)
                st.button(
                    '删除选中饰品',
                    on_click=delete_goods,
                    args=(st.session_state.inventory, selected),
                )
                st.button(
                    '出售选中饰品',
                    on_click=sell_goods,
                    args=(st.session_state.inventory, selected),
                )
                st.button(
                    '租出选中饰品',
                    on_click=lease_goods,
                    args=(st.session_state.inventory, selected),
                )
                st.button(
                    '回仓选中饰品',
                    on_click=back_goods,
                    args=(st.session_state.inventory, selected),
                )
        else:
            st.caption("暂无饰品记录")

        goods = [st.session_state.inventory()[xx] for xx in st.session_state.inventory]
        # 已购列表
        st.subheader("已购列表")
        st.text("右键表格可以导出表格")
        track = [xx for xx in goods if xx.cost != 0]
        if len(track) > 0:
            data_track = pd.DataFrame([xx() for xx in track])
            data_track['Status'] = data_track['Status'].map(
                {0: '在库中', 1: '已租出', 2: '已卖出'}
            )

            data_track.columns = [
                'Buff id',
                '有品 id',
                '名称',
                '购入花费(元)',
                'Buff 价格',
                '有品价格',
                'Steam 价格(元)',
                '状态',
                '有品在售',
                '有品在租',
                '短租价格(元)',
                '长租价格(元)',
                '押金(元)',
                '租售比',
                '理论目前收益(元)',
                '理论目前收益率(%)',
                '租金比例(%)',
                '押金比例(%)',
                '年化短租比例(%)',
                '年化长租比例(%)',
                '套现比例(%)',
                'buff和有品价格比例',
            ]
            data_track = data_track.round(4)
            #del data_track['Buff id']
            #del data_track['有品 id']
            gb0 = GridOptionsBuilder.from_dataframe(data_track)
            gb0.configure_columns(["Buff id", "有品 id", "名称"], pinned=True)
            gb0.configure_columns(
                ['理论目前收益(元)', '理论目前收益率(%)'],
                cellStyle=cellsytle_jscode,
            )
            gb0.configure_side_bar()
            gb0.configure_grid_options(domLayout='normal')

            gridOptions = gb0.build()
            grid_track = AgGrid(
                data_track,
                gridOptions=gridOptions,
                allow_unsafe_jscode=True,
                enable_enterprise_modules=True,
            )
            st.subheader("理论收益分析")
            # Plot
            x = data_track.sort_values(
                by='理论目前收益率(%)',
            )['名称'].tolist()
            y1 = data_track.sort_values(
                by='理论目前收益率(%)',
            )['理论目前收益率(%)'].tolist()
            y2 = data_track.sort_values(
                by='理论目前收益率(%)',
            )['理论目前收益(元)'].tolist()
            fig0 = (
                Bar(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
                .add_xaxis(x)
                .add_yaxis("理论目前收益率(%)", y1)
                .add_yaxis("理论目前收益(元)", y2)
                .reversal_axis()
                .set_global_opts(
                    # 设置操作图表缩放功能，orient="vertical" 为Y轴 滑动
                    datazoom_opts=[
                        opts.DataZoomOpts(),
                        opts.DataZoomOpts(type_="inside", range_start=0, range_end=100),
                        opts.DataZoomOpts(
                            orient="vertical",
                            range_start=0,
                            range_end=100,
                        ),
                    ],
                )
                # .render("bar_datazoom_both.html")
            )

            streamlit_echarts.st_pyecharts(fig0, height="900px", key="fig0")

        else:
            st.caption("暂无已购饰品")

        # 观望列表
        st.subheader("观望列表")
        observe = [xx for xx in goods if xx.cost == 0]
        if len(observe) > 0:
            data_observe = pd.DataFrame([xx() for xx in observe])
            del data_observe['Cost']
            data_observe['Status'] = data_observe['Status'].map({0: '观望中'})

            data_observe.columns = [
                'Buff id',
                '有品 id',
                '名称',
                'Buff 价格(元)',
                '有品价格(元)',
                'Steam 价格(元)',
                '状态',
                '有品在售',
                '有品在租',
                '短租价格(元)',
                '长租价格(元)',
                '押金',
                '租售比',
                '租金比例(%)',
                '押金比例(%)',
                '年化短租比例(%)',
                '年化长租比例(%)',
                '套现比例(%)',
                'buff和有品价格比例',
            ]
            data_observe = data_observe.round(4)
            del data_observe['Buff id']
            del data_observe['有品 id']
            gb1 = GridOptionsBuilder.from_dataframe(data_observe)
            gb1.configure_columns(["Buff id", "有品 id", "名称"], pinned=True)
            gb1.configure_side_bar()
            gb1.configure_grid_options(domLayout='normal')

            gridOptions = gb1.build()
            grid_observe = AgGrid(
                data_observe,
                gridOptions=gridOptions,
                allow_unsafe_jscode=True,
                enable_enterprise_modules=True,
            )

        else:
            st.caption("暂无观望饰品")


if __name__ == "__main__":
    st.set_page_config(
        "CSGO 饰品投资追踪",
        "💰",
        layout="wide",
    )
    USER_TOKEN="Bearer xxx"
    main()
