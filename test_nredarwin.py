import unittest
from suds.client import Client
import nredarwin.webservice
import os

class TestSoapClient(object):

    def __init__(self):
        self._client = Client('https://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx', nosend=True)

    def mock_response_from_file(self, operation_a, operation_b, filename=None):
        base_path = os.path.dirname(__file__)
        file_path = os.path.abspath(os.path.join(base_path, 'testdata', filename))
        fh = open(file_path, 'r')
        xml_content = fh.read()
        fh.close()
        xml_content = xml_content.encode('utf-8')
        #this is a bit odd have to get the request context which demands a message and a reply, then parse the reply using the request context
        #the message doesn't seem to do anything - so throw that away
        request_context = self._client.service[operation_a][operation_b](__inject={'msg': xml_content, 'reply': xml_content})
        return request_context.process_reply(xml_content)
        
TEST_SOAP_CLIENT = TestSoapClient()

class StationBoardTest(unittest.TestCase):

    def setUp(self):
        resp = TEST_SOAP_CLIENT.mock_response_from_file('LDBServiceSoap', 'GetDepartureBoard', filename="departure-board.xml")
        self.board = nredarwin.webservice.StationBoard(resp)

    def test_station_details(self):
        self.assertEqual(self.board.crs, 'MAN')
        self.assertEqual(self.board.location_name, 'Manchester Piccadilly')

    def test_train_service(self):
        #test a single row
        row = self.board.train_services[0]
        self.assertEqual(row.platform, "1")
        self.assertEqual(row.operator_name, "First TransPennine Express")
        self.assertEqual(row.operator_code, "TP")
        self.assertIsNone(row.sta)
        self.assertIsNone(row.eta)
        self.assertEqual(row.std, "11:57")
        self.assertEqual(row.etd, "On time")
        self.assertEqual(row.destination_text, "Middlesbrough")
        self.assertEqual(row.origin_text, "Manchester Airport")
        self.assertFalse(row.is_circular_route)
        self.assertEqual(row.service_id, "u0bRc9iGz6QPJPk0ipljgg==")

    def test_bus_services(self):
        """This board has no bus services"""
        self.assertEqual(self.board.bus_services, [])

    def test_ferry_services(self):
        """This board has no ferry services"""
        self.assertEqual(self.board.ferry_services, [])

    def test_train_service_location(self):
        #test a generic location object
        destination = self.board.train_services[0].destinations[0]
        self.assertEqual(destination.location_name, 'Middlesbrough')
        self.assertEqual(destination.crs, 'MBR')
        self.assertIsNone(destination.via)

    def test_nrcc_messages(self):
        self.assertEqual(self.board.nrcc_messages[0], 'Trains through Wembley Central&nbsp;are being delayed by up to&nbsp;40 minutes. More details can be found in <A href="    http://nationalrail.co.uk/service_disruptions/88961.aspx">Latest Travel News.</A>')

class ServiceDetailsTest(unittest.TestCase):

    def setUp(self):
        resp = TEST_SOAP_CLIENT.mock_response_from_file('LDBServiceSoap', 'GetServiceDetails', filename="service-details.xml")
        self.service_details = nredarwin.webservice.ServiceDetails(resp)

    def test_basic_details(self):
        self.assertEqual(self.service_details.sta, '15:41')
        self.assertEqual(self.service_details.eta, 'On time')
        self.assertEqual(self.service_details.std, '15:43')
        self.assertEqual(self.service_details.etd, 'On time')
        self.assertEqual(self.service_details.platform, '13')
        self.assertEqual(self.service_details.operator_name, 'East Midlands Trains')
        self.assertEqual(self.service_details.operator_code, 'EM')
        self.assertIsNone(self.service_details.ata)
        self.assertIsNone(self.service_details.atd)

    def test_messages(self):
        self.assertFalse(self.service_details.is_cancelled)
        self.assertIsNone(self.service_details.disruption_reason)
        self.assertIsNone(self.service_details.overdue_message)

    def test_calling_points(self):
        self.assertEqual(len(self.service_details.previous_calling_points), 5)
        self.assertEqual(len(self.service_details.subsequent_calling_points), 14)

    

if __name__ == '__main__':
    unittest.main()
