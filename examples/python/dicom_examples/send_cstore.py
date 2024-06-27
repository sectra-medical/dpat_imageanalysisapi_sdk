import argparse
from pydicom import dcmread
from pydicom.uid import JPEGBaseline
from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import VLWholeSlideMicroscopyImageStorage

parser = argparse.ArgumentParser(description='Send a DICOM file using C-STORE')
parser.add_argument('dcm_file', help='Path to the DICOM file to send')

args = parser.parse_args()

dcm_file = args.dcm_file

debug_logger()

dst_ip = "127.0.0.1"
dst_port = 5000
dst_title = "TARGET_AE"
src_title = "SOURCE_AE"

ae = AE(ae_title=src_title)
ae.add_requested_context(VLWholeSlideMicroscopyImageStorage, JPEGBaseline)

ds = dcmread(dcm_file)

assoc = ae.associate(dst_ip, dst_port, ae_title=dst_title)
if assoc.is_established:
    status = assoc.send_c_store(ds)

    if status:
        # If the storage request succeeded this will be 0x0000
        print('C-STORE request status: 0x{0:04x}'.format(status.Status))
    else:
        print('Connection timed out, was aborted or received invalid response')

    assoc.release()
else:
    print('Association rejected, aborted or never connected')
