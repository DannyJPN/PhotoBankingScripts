import webbrowser

def main():
    banks = {
        "ShutterStock": "https://contributor-accounts.shutterstock.com/login?next=%2Foauth%2Fauthorize%3Fstate%3Dcbbfe57e0dd0af1822d924e172a081a5%26redirect_uri%3Dhttps%253A%252F%252Fsubmit.shutterstock.com%252Foauth%252Fcallback%253Flanding_page%253Dhttps%25253A%25252F%25252Fsubmit.shutterstock.com%25252F%2526realm%253Dcontributor%26scope%3Duser.view%2520user.edit%2520media.submit%2520media.upload%2520media.edit%26site%3Dsubmit%26client_id%3DContributor",
        "AdobeStock": "https://auth.services.adobe.com/cs_CZ/index.html?callback=https%3A%2F%2Fims-na1.adobelogin.com%2Fims%2Fadobeid%2FAdobeStockClient2%2FAdobeID%2Fcode%3Fredirect_uri%3Dhttps%253A%252F%252Fstock.adobe.com%252Fcz%252F%253Fisa0%253D1%26state%3D%257B%2522ac%2522%253A%2522stock.adobe.com%2522%257D%26code_challenge_method%3Dplain%26use_ms_for_expiry%3Dtrue&client_id=AdobeStockClient2&scope=account_cluster.read%2Cadditional_info.address.mail_to%2Cadditional_info.dob%2Cadditional_info.projectedProductContext%2Cadditional_info.roles%2CAdobeID%2Ccc_private%2Ccreative_cloud%2Ccreative_sdk%2Cgnav%2Copenid%2Cread_organizations%2Cread_pc.stock%2Cread_pc.stock_credits%2Csao.cce_private%2Csao.stock%2Cstk.a.internal.cru%2Cab.manage%2Cfirefly_api&state=%7B%22ac%22%3A%22stock.adobe.com%22%7D&relay=e7989bf5-bc12-4ec2-b24a-ba0af509f6b3&locale=cs_CZ&flow_type=code&ctx_id=adbstk_c&idp_flow_type=login&s_p=google%2Cfacebook%2Capple%2Cmicrosoft&response_type=code&code_challenge_method=plain&redirect_uri=https%3A%2F%252Fstock.adobe.com%252Fcz%252F%253Fisa0%253D1&use_ms_for_expiry=true#/",
        "DreamsTime": "https://www.dreamstime.com/",
        "DepositPhotos": "https://depositphotos.com/login.html?backURL%5Bpage%5D=%2F",
        "BigStockPhoto": "https://www.bigstockphoto.com/cs/login/",
        "123RF": "https://cz.123rf.com/login/",
        "CanStockPhoto": "https://www.canstockphoto.com/",
        "Pond5": "https://www.pond5.com/",
        "GettyImages": "https://esp.gettyimages.com/sign-in?returnUrl=/contribute/batches",
        "Alamy": "https://www.alamy.com/log-in/"
    }

    for name, url in banks.items():
        try:
            webbrowser.open_new_tab(url)
            print(f"Opened {name} login page.")
        except Exception as e:
            print(f"Failed to open {name} login page. Error: {e}")

if __name__ == "__main__":
    main()