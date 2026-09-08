#include <ntddk.h>
#include <wdf.h>
#include "chm_ioctl.h"

DRIVER_INITIALIZE DriverEntry;
EVT_WDF_DRIVER_DEVICE_ADD ChmEvtDeviceAdd;
EVT_WDF_IO_QUEUE_IO_DEVICE_CONTROL ChmEvtIoDeviceControl;

NTSTATUS DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)
{
    WDF_DRIVER_CONFIG config;
    WDF_DRIVER_CONFIG_INIT(&config, ChmEvtDeviceAdd);
    return WdfDriverCreate(DriverObject, RegistryPath, WDF_NO_OBJECT_ATTRIBUTES, &config, WDF_NO_HANDLE);
}

NTSTATUS ChmEvtDeviceAdd(WDFDRIVER Driver, PWDFDEVICE_INIT DeviceInit)
{
    UNREFERENCED_PARAMETER(Driver);
    WDFDEVICE device;
    NTSTATUS status = WdfDeviceCreate(&DeviceInit, WDF_NO_OBJECT_ATTRIBUTES, &device);
    if (!NT_SUCCESS(status)) return status;

    WDF_IO_QUEUE_CONFIG queue_config;
    WDF_IO_QUEUE_CONFIG_INIT_DEFAULT_QUEUE(&queue_config, WdfIoQueueDispatchSequential);
    queue_config.EvtIoDeviceControl = ChmEvtIoDeviceControl;
    return WdfIoQueueCreate(device, &queue_config, WDF_NO_OBJECT_ATTRIBUTES, WDF_NO_HANDLE);
}

VOID ChmEvtIoDeviceControl(WDFQUEUE Queue, WDFREQUEST Request, size_t OutputBufferLength,
                           size_t InputBufferLength, ULONG IoControlCode)
{
    UNREFERENCED_PARAMETER(Queue);
    NTSTATUS status = STATUS_INVALID_DEVICE_REQUEST;
    size_t transferred = 0;

    if (IoControlCode == IOCTL_CHM_ECHO) {
        if (InputBufferLength == 0 || OutputBufferLength == 0) {
            status = STATUS_BUFFER_TOO_SMALL;
        } else {
            PVOID in_buffer = NULL;
            PVOID out_buffer = NULL;
            size_t in_size = 0, out_size = 0;
            status = WdfRequestRetrieveInputBuffer(Request, 1, &in_buffer, &in_size);
            if (NT_SUCCESS(status)) status = WdfRequestRetrieveOutputBuffer(Request, 1, &out_buffer, &out_size);
            if (NT_SUCCESS(status)) {
                transferred = (in_size < out_size) ? in_size : out_size;
                RtlCopyMemory(out_buffer, in_buffer, transferred);
            }
        }
    }
    WdfRequestCompleteWithInformation(Request, status, transferred);
}
