
# MeteoBridge Polyglot

This is the MeteoBridge Poly for the Universal Devices ISY994i](https://www.universal-devices.com/residential/ISY) [Polyglot interface](http://www.universal-devices.com/developers/polyglot/docs/) with  [Polyglot V2](https://github.com/Einstein42/udi-polyglotv2)
(c) 2018 Robert Paauwe
MIT license.

This node server is intended to support the [Meteobridge](http://www.meteobridge.com/).

## Installation

1. Backup Your ISY in case of problems!
   * Really, do the backup, please
2. Go to the Polyglot Store in the UI and install.
3. Add NodeServer in Polyglot Web
   * After the install completes, Polyglot will reboot your ISY, you can watch the status in the main polyglot log.
4. Once your ISY is back up open the Admin Console.
5. The node server should automatically run and find your hub(s) and start adding weather sensors.  It can take a couple of minutes to discover the sensors. Verify by checking the nodeserver log. 
   * While this is running you can view the nodeserver log in the Polyglot UI to see what it's doing
6. This should find your Air/Sky sensors and add them to the ISY with all the sensor values.

### Node Settings
The settings for this node are:

#### Short Poll
   * Not used
#### Long Poll
   * How often the MeteoBridge is polled for data
#### Port
   * Configure the port used to connect to live XML data from the MeteoBridge.
#### IPAddress
   * Configure the IP address of the MeteoBridge.
#### Units
   * Configure the units used when displaying data. Choices are:
   *   metric - SI / metric units
   *   us     - units generally used in the U.S.
   *   uk     - units generally used in the U.K.


## Requirements

1. Polyglot V2 itself should be run on Raspian Stretch.
  To check your version, ```cat /etc/os-release``` and the first line should look like
  ```PRETTY_NAME="Raspbian GNU/Linux 9 (stretch)"```. It is possible to upgrade from Jessie to
  Stretch, but I would recommend just re-imaging the SD card.  Some helpful links:
   * https://www.raspberrypi.org/blog/raspbian-stretch/
   * https://linuxconfig.org/raspbian-gnu-linux-upgrade-from-jessie-to-raspbian-stretch-9
2. This has only been tested with ISY 5.0.13 so it is not guaranteed to work with any other version.

# Upgrading

Open the Polyglot web page, go to nodeserver store and click "Update" for "MeteoBridge".

For Polyglot 2.0.35, hit "Cancel" in the update window so the profile will not be updated and ISY rebooted.  The install procedure will properly handle this for you.  This will change with 2.0.36, for that version you will always say "No" and let the install procedure handle it for you as well.

Then restart the MeteoBridge nodeserver by selecting it in the Polyglot dashboard and select Control -> Restart, then watch the log to make sure everything goes well.

The MeteoBridge nodeserver keeps track of the version number and when a profile rebuild is necessary.  The profile/version.txt will contain the MeteoBridge profile_version which is updated in server.json when the profile should be rebuilt.

# Release Notes

- 0.1.8 12/31/2019
   - Fix syntax error in debug log statement
- 0.1.7 12/30/2019
   - Make units lower case so comparions work properly
- 0.1.6 04/01/2019
   - Add name for total rainfall in the preciptition node.
- 0.1.5 03/20/2019
   - Fix online status going false after query.
- 0.1.4 12/15/2018
   - Fix editors for temperature and rain (inches)
- 0.1.3 11/07/2018
   - Fix wind speed conversion. It was doing kph -> mph and should be m/s -> mph
- 0.1.2 11/07/2018
   - Create nodedef directory and empty nodedef file during install.
   - Make sure nodedef directory exist before trying to write nodedef.xml file
- 0.1.1 10/26/2018
   - Restrict parsing to only look at sensor #0 records
   - Use TH record instead of THB record for temp/humidity values
- 0.1.0 09/14/2018
   - Initial version released published to github
