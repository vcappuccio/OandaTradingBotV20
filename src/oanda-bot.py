import re
import v20
import yaml

from optparse import OptionParser

class ConfigValueError(Exception):
    """
    Exception that indicates that the v20 configuration file is missing
    a required value
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Config is missing value for '{}'.".format(self.value)

class OandaBot(object):

    latest_price_time = None

    def __init__(self,config_dict={}):
        self.ssl          = config_dict['ssl']
        self.port         = config_dict['port']
        self.poll         = config_dict['poll']
        self.datetime     = config_dict['datetime']
        self.username     = config_dict['username']
        self.hostname     = config_dict['hostname']
        self.interval     = config_dict['interval']
        self.instrument   = config_dict['instrument']
        self.account_id   = config_dict['account_id']
        self.s_hostname   = config_dict['s_hostname']
        self.access_token = config_dict['access_token']

        self.api = self.create_context()

    def create_context(self):
        """
        Initialize an API context based on the Config instance
        """
        ctx = v20.Context(
            self.hostname,
            self.port, 
            self.ssl,
            application="sample_code",
            token=self.access_token,
            datetime_format=self.datetime
        )

        return ctx

    def price_to_string(self,price):
        return "{} ({}) {}/{}".format(
            price.instrument, price.time,
            price.bids[0].price, price.asks[0].price
        )
    
    
    def heartbeat_to_string(self,heartbeat):
        return "HEARTBEAT ({})".format(
            heartbeat.time
        )

    def _poll(self):
        """
        Fetch and display all prices since than the latest price time

        Args:
            OandaBot.latest_price_time: The time of the newest Price that has been seen

        Returns:
            The updated latest price time
        """

        response = self.api.pricing.get(
            self.account_id,
            #instruments=",".join(self.instrument),
            instruments="EUR_USD",
            since=OandaBot.latest_price_time,
            includeUnitsAvailable=False
        )

        #
        # Print out all prices newer than the lastest time
        # seen in a price
        #
        for price in response.get("prices", 200):
            if OandaBot.latest_price_time is None or price.time > OandaBot.latest_price_time:
                print(self.price_to_string(price))

        #
        # Stash and return the current latest price time
        #
        for price in response.get("prices", 200):
            if OandaBot.latest_price_time is None or price.time > OandaBot.latest_price_time:
                OandaBot.latest_price_time = price.time

        return OandaBot.latest_price_time

    #
    # Fetch the current snapshot of prices
    #
    #### latest_price_time = _poll(latest_price_time)

    #
    # Poll for of prices
    #
    #### while args._poll:
        #### time.sleep(args._poll_interval)
        #### latest_price_time = _poll(latest_price_time)

class Config(object):
    """
    The Config object encapsulates all of the configuration required to create
    a v20 API context and configure it to work with a specific Account.

    Using the Config object enables the scripts to exist without many command
    line arguments (host, token, accountID, etc)
    """
    def __init__(self):
        """
        Initialize an empty Config object
        """
        self.hostname = None
        self.streaming_hostname = None
        self.port = 443
        self.ssl = True
        self.token = None
        self.username = None
        self.accounts = []
        self.active_account = None
        self.path = None
        self.datetime_format = "RFC3339"

    def validate(self):
        """
        Ensure that the Config instance is valid
        """

        if self.hostname is None:
            raise ConfigValueError("hostname")
        if self.streaming_hostname is None:
            raise ConfigValueError("hostname")
        if self.port is None:
            raise ConfigValueError("port")
        if self.ssl is None:
            raise ConfigValueError("ssl")
        if self.username is None:
            raise ConfigValueError("username")
        if self.token is None:
            raise ConfigValueError("token")
        if self.accounts is None:
            raise ConfigValueError("account")
        if self.active_account is None:
            raise ConfigValueError("account")
        if self.datetime_format is None:
            raise ConfigValueError("datetime_format")

if __name__ == "__main__":
    
    parser = OptionParser()
    parser.add_option('-i', '--instrument',
        dest='instrument', default='EUR_USD',
        help='Default instrument.')
    parser.add_option('-p','--poll',
        dest='poll', action='store_true', default=False,
        help='Flag used to poll repeatedly for price updates')
    parser.add_option('-y','--use-yaml',
        dest='yaml', action='store_true', default=False,
        help='Use yaml file for configuration variables.')
    parser.add_option('--poll-interval',
        dest='interval',type=float, default=2,
        help="The interval between polls. Only relevant polling is enabled")
    parser.add_option('-D', '--datetime-format',
        dest='datetime', default='RFC3339',
        help='Datetime format.')

    parser.add_option('--ssl',
        dest='ssl', action='store_true', default=True,
        help='Enable SSL. Defaults to True.')
    parser.add_option('-P', '--port',
        dest='port',type=int, default=443,
        help='Default port to send API call over.')
    parser.add_option('-S', '--streaming-host',
        dest='s_hostname', default='api-fxtrade.oanda.com',
        help='Streaming hostname to send API call to.')
    parser.add_option('-H', '--host',
        dest='hostname', default='api-fxtrade.oanda.com',
        help='Hostname to send API call to.')
    parser.add_option('-U', '--username',
        dest='username', default=str(),
        help='Username to log into Oanda with.')
    parser.add_option('--account-id',
        dest='account_id', default=str(),
        help='Account id to login to Oanda with.')
    parser.add_option('--access-token',
        dest='access_token', default=str(),
        help='Access token to authenticate on Oanda with.')
    (options, args) = parser.parse_args()

    if options.yaml:

        with open('/home/anthony/.v20.yml', 'r') as file:
            config = yaml.safe_load(file)
            
        opts = [
            'options.username','options.access_token','options.account_id',
            'options.ssl','options.port','options.hostname','options.s_hostname'
        ]

        for opt in opts:
            try:
                key = re.sub('options.','',opt)
                setattr(options,key,config['production'][key])
            except KeyError:
                pass

    config_dict = {
        'ssl': options.ssl,
        'port': options.port,
        'poll': options.poll,
        'datetime': options.datetime,
        'hostname': options.hostname,
        's_hostname': options.s_hostname,
        'instrument': options.instrument,
        'username': options.username,
        'interval': options.interval,
        'account_id': options.account_id,
        'access_token': options.access_token,
    }

bot = OandaBot(config_dict)
bot._poll()
