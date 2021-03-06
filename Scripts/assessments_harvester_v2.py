#import required modules
import exceptions
import urllib2, json
from cartodb import CartoDBAPIKey, CartoDBException

#cartodb variables
api_key = 'ebd93f0d0daf2ab7d2b31e2449e307cfe0744252'
cartodb_domain = 'troy'
cl = CartoDBAPIKey(api_key, cartodb_domain)

def insert_into_cartodb(sql_query):
    try:
       # your CartoDB account:
        print cl.sql(sql_query)
    except CartoDBException as e:
       print ("some error ocurred", e)
       
def get_max_id():
    return cl.sql('SELECT MAX(id) FROM humanitarian_response')['rows'][0]['max']

#parse the json
def getResults(data):
  # Use the json module to load the string data into a dictionary
  api_url = json.loads(data)
  
  for i in api_url["data"]:
    #defining the variables that will be pulled into CartoDB
    id = i["id"]
    label = i["label"]
    cluster_id = i["bundles"][0]["id"]
    cluster_label = i["bundles"][0]["label"]
    location_id = i["locations"][0]["id"]
    location_label = i["locations"][0]["label"]
    
    #function to retreive data from nested locations JSON
    def getLocation():
        location_api = i["locations"][0]["self"]
        print " "
        openlocations = urllib2.urlopen(location_api)
        
        #checks connection and loads the json
        if (openlocations.getcode() == 200):
            location_data = openlocations.read()
            load_locations = json.loads(location_data)
            
            #defining variables as global so they can be used outside of this function
            global geo_id
            geoid = load_locations["data"][0]["id"]
            global geo_pcode
            geo_pcode = load_locations["data"][0]["pcode"]
            global geo_iso_code
            geo_iso_code = load_locations["data"][0]["iso3"]
            global lat
            lat = load_locations["data"][0]["geolocation"]["lat"]
            global long
            long = load_locations["data"][0]["geolocation"]["lon"]
         #prints error mesage if connection fails   
        else:
            print "Received an error from the server and cannot retrieve the results" + str(openlocations.getcode())
    getLocation()
    
    print str(id) + "\t" + str(label) + "\t" + str(cluster_id) + "\t" + str(cluster_label) + "\t" + str(location_id) + "\t" + str(location_label) + "\t" + str(lat) + "\t" + str(long)
     
    
#creating the CartoDB insert
def create_sql_statement(long, lat, id, label, cluster_id, cluster_label, location_id, location_label):
    # Start with a basic INSERT statement
    # -> Don't forget to replace with your table name
    sql_query = 'INSERT INTO humanitarian_response (the_geom, id, label, cluster_id, cluster_label, location_id, location_label) VALUES ('

    # Add our values to the statement, making sure that we wrap string values
    # in quotes
    # 4/8, EB: Fixed bug on next line that rounded x/y down to very low
    # precision
    sql_query = sql_query + "'SRID=4326; POINT (%f %f)', '%s', '%s', '%s', '%s', '%s', '%s'" % (long, lat, id, label, cluster_id, cluster_label, location_id, location_label)
    sql_query = sql_query + ')'  
    return str(sql_query)
  
def main():
  # define a variable to hold the source URL
  urlData = "http://www.humanitarianresponse.info/api/v1.0/assessments"
  
  # Open the URL and read the data
  webUrl = urllib2.urlopen(urlData)
  if (webUrl.getcode() == 200):
    data = webUrl.read()
    # print out our customized results
    getResults(data)
    # This is where you call insert_into_cartodb()
    insert_into_cartodb(sql_query)
  else:
    print "Received an error from server, cannot retrieve results " + str(webUrl.getcode())

if __name__ == "__main__":
  main()
  try:
    cl.sql('DELETE FROM humanitarian_response WHERE cartodb_id NOT IN (SELECT MIN(cartodb_id) FROM humanitarian_response GROUP BY id)')
  except CartoDBException as e:
    print ("some error ocurred", e)