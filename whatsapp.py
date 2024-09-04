import contextlib
import logging
import os
import re
import shutil
import time
import ctypes
from datetime import datetime
from os.path import exists
from zipfile import ZipFile, BadZipFile

import requests
from selenium.webdriver import Keys
from webdriver_manager.chrome import ChromeDriverManager
from subprocess import CREATE_NO_WINDOW
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, StaleElementReferenceException, \
    TimeoutException, InvalidSessionIdException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import MyApp
import facebook
import twitter

logger = logging.getLogger()


# Class contenant tous les composants de la page web de whatsapp nécessaire dans le code
class WhatsAppElements:
    path = f'{os.getcwd()}\\Configuration\\whatsappelements.txt'
    if exists(path):
        try:
            # Ouverture et lecture du fichier
            f = open(path, "r")
            values = list(f.read().split("\n"))
            # Attribution des références
            # Champs de recherche de destinataire
            search = (By.CSS_SELECTOR, values[0])
            conversationDiv = (By.CSS_SELECTOR, values[1])
            existingConversation = (By.CSS_SELECTOR, values[2])
            nameConversation = (By.CSS_SELECTOR, values[3])
            notificationElement = (By.CSS_SELECTOR, values[4])
            lstMessages = (By.CSS_SELECTOR, values[5])
            lienElement = (By.CSS_SELECTOR, values[6])
            contactElement = (By.CSS_SELECTOR, values[7])
            conversationInput = (By.CSS_SELECTOR, values[8])
            # Info du message (en cours, distribué, lu)
            messageTime = (By.CSS_SELECTOR, values[9])
            messageCheck = (By.CSS_SELECTOR, values[10])
            messageDoubleCheck = (By.CSS_SELECTOR, values[11])
        except Exception as error:
            logger.error("Erreur lors de la lecture de whatsappelements " + str(error))
    else:
        logger.info("Aucun fichier de whatsappelements")


# Méthode pour contrôler la compatibilité de version entre le navigateur chrome et le chromedriver télécharger en local
def checkChromedriverVersion():
    # instanciation d'un navigateur
    driver = webdriver.Chrome()
    # numéro de version du navigateur
    browserVersion = driver.capabilities['browserVersion']
    # numéro de version du chromedriver
    chromeDriverVersion = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]
    # return sous format tuple du resultat de la comparaison et de la version du navigateur
    return str(browserVersion[0:3]).__eq__(str(chromeDriverVersion[0:3])), browserVersion


# Méthode de mise à jour du chromedriver avec en paramètre la version du navigateur chrome
def updateChromedriverVersion(chromeWantedVersion=None):
    # URL de telechargement de la version souhaité. Il n'est pas possible de download a la vole une version d'un chromedriver.
    # une version doit etre specifie afin que le telechargement fonctionne
    driverURL = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{chromeWantedVersion}/win32/chromedriver-win32.zip"
    # nommage de l'output
    output = driverURL.split('/')[-1]
    # telechargement du zip
    r = requests.get(driverURL)
    with open(output, 'wb') as f:
        # ecriture du zip en local
        f.write(r.content)
        f.close()
    try:
        with ZipFile(output, 'r') as zObject:
            # dézip du fichier archive
            zObject.extractall(path=".\\")
            # replace du chromedriver afin d'en modifier le chemin et le deplacer vers le repertoire indique dans la variable environnement systeme dediee
            # rename ne fonctionne pas si un chromedriver existe déjà car dépendant des droits utilisateurs windows pour pouvoir overwrite
            os.replace(f"./{zObject.namelist()[1]}", str(os.environ.get("Chromedriver")))
            zObject.close()
            logger.info(f"Mise à jour du chromedriver vers la version {chromeWantedVersion}")

        # suppression du zip
        os.remove(output)
        # suppression du fichier dezippé
        shutil.rmtree(f'./{output.split(".")[0]}')

    except BadZipFile:
        logger.error(
            f"La version du chromedriver {chromeWantedVersion} n'est pas disponible sur les repo de Google ")
        ctypes.windll.user32.MessageBoxW("Mise à jour du chromedriver impossible par l'application")
    except Exception as e:
        logger.error(
            "Une erreur non identifiée est survenue lors du téléchargement de la mise à jour du chromedriver")
        logger.error(str(e))
        ctypes.windll.user32.MessageBoxW(
            "Une erreur non identifiée ne permet pas à l'application de mettre à jour le chromedriver")


# This class is used to interact with your whatsapp [UNOFFICIAL API]
class WhatsApp:
    browser = None
    timeout = 31536000  # durée timeout serveur
    lastSeenURL = ""
    screen = None
    listContributeurs = {}
    chrome_path = None
    chrome_service = None
    chrome_options = None

    def goToHomePage(self):
        self.browser.get("https://web.whatsapp.com/")
        # Attente de la localisation du champ de recherche d'un contact pour s'assurer que la fenêtre soit chargée complètement.
        WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(WhatsAppElements.search))

    def goToHomePageAfterFacebook(self):
        logger.info("Retour WhatsApp homepage")
        self.browser.get("https://web.whatsapp.com/")
        # Attente de la localisation du champ de recherche d'un contact pour s'assurer que la fenêtre soit chargée complètement.
        WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(WhatsAppElements.search))
        # Clic sur la premiere conversation
        conversations = self.browser.find_elements(*WhatsAppElements.nameConversation)
        WebDriverWait(self.browser, self.timeout).until(EC.element_to_be_clickable(conversations[0]))
        conversations[0].click()

    # Constructeur
    def __init__(self, wait, screenshot=None, session=None, screen=None):
        try:

            self.loadContributeurs()
            self.screen = screen
            # Désactivation du bouton Lancer l'écoute
            self.screen.ids.LaunchButton.disabled = True
            # Gestion du chromedriver par son manager.
            # Il contrôle au lancement la version du chromedriver et met à jour si nécessaire.
            # self.chrome_path = ChromeDriverManager().install()

            # contrôle de la version du chromedriver
            versionCompatible = checkChromedriverVersion()
            if not versionCompatible[0]:
                # mise à jour du chromedriver
                updateChromedriverVersion(chromeWantedVersion=versionCompatible[1])
            self.chrome_path = str(os.environ.get('Chromedriver'))
            self.chrome_service = Service(self.chrome_path)
            self.chrome_service.creation_flags = CREATE_NO_WINDOW

            # Si une session est renseignée
            if session:
                # création de chrome_options pour passer le chemin vers la session en argument de connexion pour passer l'étape QR code
                self.chrome_options = Options()
                self.chrome_options.add_argument("--user-data-dir={}".format(session))
                self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
                with contextlib.redirect_stdout(None):
                    self.browser = webdriver.Chrome(options=self.chrome_options,
                                                    service=self.chrome_service)  # we are using chrome as our webbrowser
                logger.info("Lancement de la session WhatsApp avec la session renseignée")

            else:
                # Sinon création d'une connexion sans session
                self.browser = webdriver.Chrome(service=self.chrome_service)
                logger.info("Lancement de la session WhatsApp sans session")

        except Exception as e:
            if isinstance(e, WebDriverException):
                self.screen.ids.LaunchButton.disabled = False
                MB_SYSTEMMODAL = 0x00001000
                ctypes.windll.user32.MessageBoxW(0,
                                                 "Lancement de la nouvelle session impossible, une fenêtre Chrome lancé par HEIMDALL semble être toujours active.",
                                                 "Erreur", MB_SYSTEMMODAL)
                logger.error(
                    "WP : Lancement de la nouvelle session impossible, une fenêtre Chrome lancé par HEIMDALL est toujours active.")

            else:
                self.screen.ids.LaunchButton.disabled = False
                MB_SYSTEMMODAL = 0x00001000
                ctypes.windll.user32.MessageBoxW(0,
                                                 "Lancement de la nouvelle session impossible. Vérifiez votre connexion internet",
                                                 "Erreur", MB_SYSTEMMODAL)
                logger.error("WP : Lancement de la nouvelle session impossible suite à une erreur inconnue.")

        # Requête vers l'url de WhatsApp
        if self.browser is not None:
            self.goToHomePage()

    def loadContributeurs(self):
        if os.path.exists("Configuration\contributeurs.txt"):
            with open(f"{os.getcwd()}\Configuration\contributeurs.txt", "r") as file:
                for val in file.readlines():
                    valsplit = val.split(';')
                    # Contributeur : nom ; nombre de liens partagés
                    self.listContributeurs.update({valsplit[0]: int(valsplit[1])})
                file.close()
                logger.info("Chargement des contributeurs")
        else:
            logger.error("Fichier des contributeurs inexistant")

    def saveContributeurs(self):
        if not os.path.exists("Configuration\contributeurs.txt"):
            ctypes.windll.user32.MessageBoxW(0,
                                             "Le fichier des contributeurs n'est pas présent dans le répertoire de HEIMDALL\Configuration.\n"
                                             "Veuillez le recréer ou procéder à une nouvelle installation",
                                             "Erreur")
            return
        try:
            with open("Configuration\contributeurs.txt", 'w') as file:
                saveStr = ""
                for contribName, contribCount in self.listContributeurs.items():
                    # Contributeur : nom ; nombre de liens partagés
                    saveStr += str(contribName) + ";" + str(contribCount) + "\n"
                file.write(saveStr)
                file.close()
        except Exception as error:
            logger.error("Problème lors de la sauvegarde des contributeurs " + str(error))
            ctypes.windll.user32.MessageBoxW(0, "Erreur lors de la sauvegarde des contributeurs", "Erreur")

    def checkIfURL(self, message=None):
        try:
            # Regex url
            regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            url = re.findall(regex, message)
            if len([x[0] for x in url]) > 0:
                # Contrôle si le dernier message de la conversation est bien le dernier message traité
                if [x[0] for x in url][0] != self.lastSeenURL:
                    self.lastSeenURL = [x[0] for x in url][0]
                    return [x[0] for x in url]
                else:
                    return []
            else:
                return []
        except Exception as e:
            logger.error("checkIfURL : " + str(e))

    def handleContent(self, message=None, savePath=None, screen=None):
        # Contrôle si le chemin contient url
        response = self.checkIfURL(message)
        if len(response) > 0:
            # Contrôle du contenu de l'url pour répartir vers le bon handle
            if str(response[len(response) - 1]).__contains__("twitter"):
                twitter.handleTwitter(url=response,
                                      extract=str(response[len(response) - 1]).split("/")[-1].split("?")[0],
                                      savePath=savePath, screen=screen)
                return True
            elif str(response[len(response) - 1]).__contains__("facebook") or str(
                    response[len(response) - 1]).__contains__("fb.watch"):
                time.sleep(1)
                try:
                    facebook.handleFacebookURL(url=response[len(response) - 1], browser=self.browser,
                                               savePath=savePath, screen=screen)
                    # Retour vers l'accueil de WhatsApp car le bot est à cette étape sur l'url Facebook
                    self.goToHomePageAfterFacebook()
                    return True
                except Exception as e:
                    logger.error("Facebook : " + str(e))
                    self.goToHomePageAfterFacebook()
                    return False
            elif str(response[len(response) - 1]).__contains__("instagram"):
                logger.info("Plateforme instagram non implémenté")
                return False
            else:
                logger.error("URL non pris en charge")
                return False
        return False

    def listeningForNewMessage(self, savePath):
        while True:
            divContainer = self.browser.find_element(*WhatsAppElements.conversationDiv)
            for contact in divContainer.find_elements(*WhatsAppElements.existingConversation):
                try:
                    # Recherche d'une notification parmis les conversations
                    if contact.find_element(*WhatsAppElements.notificationElement):
                        return
                except Exception as error:
                    # Si pas de notification alors exception et écoute des messages de la conversation courante
                    try:
                        # Liste des messages de la conversation
                        divMessage = self.browser.find_element(*WhatsAppElements.lstMessages)
                        liens = divMessage.find_elements(*WhatsAppElements.lienElement)
                        contributeurs = divMessage.find_elements(*WhatsAppElements.contactElement)
                        # Contrôle du contenu pour chercher un lien vers twitter / FB / autre
                        if self.handleContent(message=liens[-1].text, savePath=savePath, screen=self.screen):
                            if len(contributeurs) != 0:
                                # Mise à jour des contributeurs
                                try:
                                    self.listContributeurs[contributeurs[-1].text] += 1
                                except KeyError:
                                    self.listContributeurs[contributeurs[-1].text] = 1
                                self.saveContributeurs()
                            else:
                                logger.info("Le contact est connu, merci de le retirer de vos contacts.")
                            if "$" in liens[-1].text:
                                # Transfère du lien au groupe signalé par le $
                                self.send_alert(liens[-1].text)
                    except NoSuchElementException as error:
                        logger.error(error)
                        mymessage = 'Erreur suite à une mise à jour WhatsApp'
                        title = 'Contactez la 785'
                        ctypes.windll.user32.MessageBoxW(0, mymessage, title, 0)
                    except Exception as error:
                        logger.error("ListeningForNewMessage : " + str(error))
                        break
                    time.sleep(1)
                    continue

    def listenNewMessage(self, savePath):
        # Récupération de l'horaire de rapport dans config.txt
        if os.path.exists("Configuration\config.txt"):
            with open(f"{os.getcwd()}\Configuration\config.txt", "r") as file:
                values = []
                for line in file.readlines():
                    values.append(line)
                heureRapport = datetime.strptime(values[3].strip(), "%H:%M:%S").time()
                file.close()
                logger.info("Chargement de la configuration")
        else:
            logger.error("Fichier de configuration inexistant")
        while True:
            try:
                # Contrôle de l'horaire et si le rapport a déjà été envoyé pour déclencher son envoi
                now = datetime.now().time()
                if now < heureRapport and MyApp.VeilleScreen.rapportIsDone is True:
                    MyApp.VeilleScreen.rapportIsDone = False
                    MyApp.saveStats()
                if now > heureRapport and MyApp.VeilleScreen.rapportIsDone is False:
                    self.send_rapport(savePath=savePath)
            except Exception as e:
                logger.error("Rapport : " + str(e))
            try:
                # div pour toutes les conversations
                divContainer = self.browser.find_element(*WhatsAppElements.conversationDiv)
                WebDriverWait(self.browser, 60).until(
                    EC.element_to_be_clickable(WhatsAppElements.existingConversation))
                time.sleep(1)
                # Toutes les conversations dans la div dédiée
                for contact in divContainer.find_elements(*WhatsAppElements.existingConversation):
                    # Composant pour la pastille verte des nouveaux messages
                    try:
                        if contact.find_element(*WhatsAppElements.notificationElement):
                            # Nombre de nouveaux messages indiqué dans le composant
                            nbNewMessage = int(contact.find_element(*WhatsAppElements.notificationElement).text)
                            # Sélection du contact afin d'accéder au contenu de la conversation
                            contact.click()
                            # Composant où s'affiche les messages
                            messagesListe = WebDriverWait(self.browser, 60).until(
                                EC.presence_of_element_located(WhatsAppElements.lstMessages))
                            # Récupération de tous les messages
                            try:
                                liens = messagesListe.find_elements(*WhatsAppElements.lienElement)
                                contributeurs = messagesListe.find_elements(*WhatsAppElements.contactElement)
                                # reversed permet de parcourir le tableau dans le sens inverse afin de partir du dernier message reçu
                                # enumerate calcul le volume de la liste
                                # Parcours de la liste depuis le dernier message et on remonte d'autant de messages que la variable "nbNewMessage"
                                for index, message in enumerate(reversed(liens)):
                                    if index < nbNewMessage:
                                        # Contrôle du contenu pour chercher un lien vers twitter / FB / autre
                                        if self.handleContent(message=message.text, savePath=savePath,
                                                              screen=self.screen):
                                            # Mise à jour des contributeurs
                                            if len(contributeurs) != 0:
                                                try:
                                                    self.listContributeurs[contributeurs[-1].text] += 1
                                                except KeyError:
                                                    self.listContributeurs[contributeurs[-1].text] = 1
                                                self.saveContributeurs()
                                            else:
                                                logger.info(
                                                    "Le contact est connu, merci de le retirer de vos contacts.")
                                            if "$" in message.text:
                                                # Transfère du lien au groupe signalé par le $
                                                self.send_alert(message.text)
                                    else:
                                        break
                            except NoSuchElementException as error:
                                logger.error(error)
                                mymessage = 'Erreur suite à une mise à jour WhatsApp'
                                title = 'Contactez la 785'
                                self.screen.ids.LaunchButton.disabled = False
                                ctypes.windll.user32.MessageBoxW(0, mymessage, title, 0)
                            except Exception as err:
                                logger.error("listContributeurs : " + str(err))
                            # Au sein d'une conversation, les nouveaux messages ne sont pas pris en compte par le code au-dessus car nous sommes déjà dans la conversation donc il n'y a pas de notification.
                            # La méthode ci-dessous va écouter en boucle la conversation jusqu'à ce qu'une notification pour un nouveau message dans une autre conversation soit affichée.
                            self.listeningForNewMessage(savePath)
                        else:
                            continue
                    except NoSuchElementException as e:
                        pass
                    except StaleElementReferenceException as e:
                        logger.error(e)
                    except Exception as e:
                        logger.error("ListenNewMessage : " + str(e))
                        self.screen.ids.LaunchButton.disabled = False
                    # Continue pour passer au prochain contact quand une notification n'est pas trouvée sur le contact courant
                    continue
            except InvalidSessionIdException as idException:
                logger.error("ListenNewMessage session ID : " + str(idException))
                return

    def send_rapport(self, savePath=None):
        if os.path.exists("Configuration\config.txt"):
            with open(f"{os.getcwd()}\Configuration\config.txt", "r") as file:
                values = []
                for line in file.readlines():
                    values.append(line)
                messageSupp = values[2]
                file.close()
                logger.info("Chargement de la configuration")
        else:
            logger.error("Fichier de configuration inexistant")
        try:
            max_name = max(self.listContributeurs, key=self.listContributeurs.get)
            max_count = max(self.listContributeurs.values())
            message = f"Aujourd'hui nous comptabilisons {str(MyApp.VeilleScreen.totalCount)} liens dont {str(MyApp.VeilleScreen.twitterCount)} de Twitter et {str(MyApp.VeilleScreen.facebookCount)} de Facebook." \
                      f"Merci à {max_name} pour ses {max_count} liens. {messageSupp}"
            # Liste des conversations
            divContainer = self.browser.find_element(*WhatsAppElements.conversationDiv)
            for contact in divContainer.find_elements(*WhatsAppElements.existingConversation):
                contact.click()
                # Sélection du champ de saisi dès qu'il est cliquable
                send_msg = WebDriverWait(self.browser, self.timeout).until(
                    EC.element_to_be_clickable(WhatsAppElements.conversationInput))
                # Cast en string pour éviter les erreurs
                messages = str(message).split("\n")
                # Envoi du message
                for msg in messages:
                    send_msg.send_keys(msg)
                    send_msg.send_keys(Keys.ENTER)
                    time.sleep(1)
                # Attente de la confirmation de l'envoi
                try:
                    time.sleep(1)
                    WebDriverWait(self.browser, 10).until_not(EC.element_to_be_clickable(WhatsAppElements.messageTime))
                except TimeoutException:
                    try:
                        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(WhatsAppElements.messageCheck))
                    except TimeoutException:
                        WebDriverWait(self.browser, 10).until(
                            EC.element_to_be_clickable(WhatsAppElements.messageDoubleCheck))

            # Archivage du fichier de veille Twitter
            try:
                if not os.path.exists(savePath + "/archives"):
                    os.makedirs(savePath + "/archives")
                dateFichier = (datetime.now().strftime("%Y%m%d"))
                if os.path.exists(f"{savePath}/veille_ffs_twitter.csv"):
                    shutil.move(f"{savePath}/veille_ffs_twitter.csv",
                                f"{savePath}/archives/{dateFichier}_ffs_twitter.csv")
            except Exception as error:
                logger.error("Problème lors de la création du répertoire d'archive " + str(error))
                ctypes.windll.user32.MessageBoxW(0, "Erreur de la création du répertoire d'archive", "Erreur")

            MyApp.VeilleScreen.twitterCount = 0
            MyApp.VeilleScreen.facebookCount = 0
            MyApp.VeilleScreen.totalCount = 0
            MyApp.VeilleScreen.rapportIsDone = True
            MyApp.saveStats()
            for contrib, count in self.listContributeurs.items():
                self.listContributeurs[contrib] = 0
            self.saveContributeurs()
        except InvalidSessionIdException as invalidSession:
            logger.error("Internet indisponible : " + str(invalidSession))

    def send_alert(self, message=str):
        try:
            messageSplit = message.split("$")
            # Le lien dans le message
            url = messageSplit[0]
            # Le groupe destinataire
            dest = messageSplit[1]
            conversations = self.browser.find_elements(*WhatsAppElements.nameConversation)
            for nom in conversations:
                if dest == nom.text:
                    WebDriverWait(self.browser, self.timeout).until(EC.element_to_be_clickable(nom))
                    nom.click()
                    # Sélection du champ de saisi dès qu'il est cliquable
                    send_msg = self.browser.find_element(*WhatsAppElements.conversationInput)
                    # Cast en string pour éviter les erreurs
                    messages = str(url).split("\n")
                    # Envoi du message
                    for msg in messages:
                        send_msg.send_keys(msg)
                        send_msg.send_keys(Keys.ENTER)
                        time.sleep(1)
        except Exception as error:
            logger.error("send_alert : " + str(error))
