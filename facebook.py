from os.path import exists

from bs4 import BeautifulSoup
from selenium import webdriver
import time
import os
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import MyApp
import logging

logger = logging.getLogger()

def handleFacebookURL(url=None, browser=None, savePath=None, screen=None):
    if str(url).__contains__("posts"):
        scrapPost(url, browser, savePath)
    elif str(url).__contains__("story"):
        scrapStory(url, browser, savePath)
    elif str(url).__contains__("fb.watch"):
        scrapWatch(url, browser, savePath)
    else:
        scrapUser(url, browser, savePath)

    # Mise à jour des labels pour afficher les résultats
    MyApp.VeilleScreen.facebookCount += 1
    MyApp.VeilleScreen.totalCount += 1
    MyApp.saveStats()

    MyApp.updateResultVeille(screen=screen)


def scrapUser(url=None, browser=None, savePath=None):
    target_url = url
    browser.get(target_url)
    time.sleep(5)

    extractUser = url.split('/')[3]
    resp = browser.page_source

    soup = BeautifulSoup(resp, 'html.parser')

    # recupération adresse tel et email
    items = soup.find_all('div', {
        'class': 'x9f619 x1n2onr6 x1ja2u2z x78zum5 x2lah0s x1qughib x1qjc9v5 xozqiw3 x1q0g3np x1pi30zi x1swvt13 xyamay9 xykv574 xbmpl8g x4cne27 xifccgj'})[
        1]

    allDetails = items.find_all("div", {
        "class": "x9f619 x1n2onr6 x1ja2u2z x78zum5 x2lah0s x1nhvcw1 x1qjc9v5 xozqiw3 x1q0g3np xyamay9 xykv574 xbmpl8g x4cne27 xifccgj"})

    adresse = number = email = ""
    for contact in allDetails:
        checkaddress = len(contact.text.split(","))
        if checkaddress > 2:
            try:
                adresse = contact.text
            except:
                adresse = None
            continue

        contactNumber = contact.text.replace("-", "").replace("+", "").replace(" ", "")

        if contactNumber.isnumeric():
            try:
                number = contactNumber
            except:
                number = None
            continue

        if '@' in contact.text:
            try:
                email = contact.text
            except:
                email = None
            continue

    # recuperations du nombre de likes et followers
    items = soup.find_all('a', {
        'class': 'x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xi81zsa x1s688f'})

    resultScrapUserFacebook = []

    likes = items[0].text.split(" ")
    followers = items[1].text.split(" ")
    intro = soup.find('div', {
        'class': 'x2b8uid xdppsyt x1l90r2v'})
    data = [url, extractUser, likes[0], followers[0], intro.text, adresse, number, email]
    resultScrapUserFacebook.append(data)

    user_facebook_csv = pd.DataFrame(
        resultScrapUserFacebook, columns=["url", "user", "likes", "followers", "intro", "adresse", "number", "email"]
    )
    try:
        pathFile = f"{savePath}\export_facebook_User_veille.csv"
        user_facebook_csv.to_csv(f"{savePath}\export_facebook_User_veille.csv", index=False, sep="|",
                                 quoting=csv.QUOTE_MINIMAL,
                                 mode='a', header=not os.path.exists(pathFile),   encoding="cp1252", errors='replace')
    except Exception as e:
        logger.error(e)

def scrapPost(url=None, browser=None, savePath=None):
    target_url = url

    browser.get(target_url)
    time.sleep(5)

    #recup des infos du post
    extractUser = url.split('/')[3]

    #recup des elements facebook
    path = f'{os.getcwd()}\\Configuration\\facebookelements.txt'
    if exists(path):
        try:
            # ouverture et lecture du fichier
            f = open(path, "r")
            values = list(f.read().split("\n"))
            contenuPost = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[0])))
            nbjoursPost = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[1])))
            nbJaimePost = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[2])))

            resultScrapPost = []

            data = [url, extractUser, contenuPost.text.split('\n'), nbjoursPost.text, nbJaimePost.text]
            resultScrapPost.append(data)

            post_facebook_csv = pd.DataFrame(
                resultScrapPost, columns=["url", "user", "contenu", "nb jours post", "nb jaime"]
            )
            try:
                pathFile = f"{savePath}\export_facebook_Posts_veille.csv"
                post_facebook_csv.to_csv(f"{savePath}\export_facebook_Posts_veille.csv", index=False, sep="|", quoting=csv.QUOTE_MINIMAL,
                                 mode='a', header=not os.path.exists(pathFile),   encoding="cp1252", errors='replace')
            except Exception as e:
                logger.error(e)
        except Exception as error:
            logger.error("Erreur lors de la lecture de facebookelements " + str(error))
    else:
        logger.info("Aucun fichier de facebookelements")

def scrapStory(url=None, browser=None, savePath=None):
    target_url = url
    browser.get(target_url)
    time.sleep(5)
    # recup des elements facebook
    path = f'{os.getcwd()}\\Configuration\\facebookelements.txt'
    if exists(path):
        try:
            # ouverture et lecture du fichier
            f = open(path, "r")
            values = list(f.read().split("\n"))
            #recup des infos de a story
            userStory = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[3])))
            dateStory = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[4])))
            contenu = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[5])))

            resultScrapStory = []
            data = [url, userStory.text, dateStory.text, contenu.text.split('\n')]
            resultScrapStory.append(data)

            story_facebook_csv = pd.DataFrame(
                resultScrapStory, columns=["url", "user", "date story", "contenu"]
            )
            try:
                pathFile = f"{savePath}\export_facebook_Story_veille.csv"
                story_facebook_csv.to_csv(f"{savePath}\export_facebook_Story_veille.csv", index=False, sep="|", quoting=csv.QUOTE_MINIMAL,
                                 mode='a', header=not os.path.exists(pathFile),   encoding="cp1252", errors='replace')
            except Exception as e:
                logger.error(e)
        except Exception as error:
            logger.error("Erreur lors de la lecture de facebookelements " + str(error))
    else:
        logger.info("Aucun fichier de facebookelements")

def scrapWatch(url=None, browser=None, savePath=None):
    target_url = url
    browser.get(target_url)
    time.sleep(5)

    # recup des elements facebook
    path = f'{os.getcwd()}\\Configuration\\facebookelements.txt'
    if exists(path):
        try:
            # ouverture et lecture du fichier
            f = open(path, "r")
            values = list(f.read().split("\n"))
            #recup des infos de la video
            userWatch = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[6])))
            dateStory = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[7])))
            nb_jaime = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[8])))
            nb_comments = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[9])))
            nb_vues = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, values[10])))

            resultScrapStory = []

            data = [url, userWatch.text, dateStory.text, nb_jaime.text, nb_comments.text.split(" ")[0], nb_vues.text.split(" ")[0]+nb_vues.text.split(" ")[1]]
            resultScrapStory.append(data)

            story_facebook_csv = pd.DataFrame(
                resultScrapStory, columns=["url", "user", "date_video", "nb_jaime_video", "nb_comments_video", "nb_vues_video"]
            )
            try:
                pathFile = f"{savePath}\export_facebook_Watch_veille.csv"
                story_facebook_csv.to_csv(f"{savePath}\export_facebook_Watch_veille.csv", index=False, sep="|", quoting=csv.QUOTE_MINIMAL,
                                 mode='a', header=not os.path.exists(pathFile),   encoding="cp1252", errors='replace')
            except Exception as e:
                logger.error(e)

        except Exception as error:
            logger.error("Erreur lors de la lecture de facebookelements " + str(error))
    else:
        logger.info("Aucun fichier de facebookelements")