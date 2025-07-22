import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Snackbar,
  Alert,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import AddCameraForm from './AddCameraForm';
import { CreateCameraRequest } from '../types/camera';
import { cameraService } from '../services/camera.service';

interface AddCameraModalProps {
  open: boolean;
  onClose: () => void;
  onCameraAdded?: () => void;
}

const AddCameraModal: React.FC<AddCameraModalProps> = ({
  open,
  onClose,
  onCameraAdded,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');

  const handleSubmit = async (cameraData: CreateCameraRequest) => {
    setIsLoading(true);
    setError('');

    try {
      const response = await cameraService.createCamera(cameraData);

      if (response.status === 'success') {
        setSuccessMessage(`Camera "${cameraData.name}" created successfully!`);
        // Close modal after a short delay to show success message
        setTimeout(() => {
          handleClose();
          if (onCameraAdded) {
            onCameraAdded();
          }
        }, 1500);
      } else {
        setError(response.message);
      }
    } catch (error: any) {
      setError('An unexpected error occurred while creating the camera.');
      console.error('Error creating camera:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setError('');
    setSuccessMessage('');
    setIsLoading(false);
    onClose();
  };

  const handleSnackbarClose = () => {
    setSuccessMessage('');
  };

  return (
    <>
      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="md"
        fullWidth
        scroll="paper"
        PaperProps={{
          sx: {
            minHeight: '600px',
            maxHeight: '90vh',
          },
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            pr: 1,
          }}
        >
          Add New Camera
          <IconButton
            onClick={handleClose}
            disabled={isLoading}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent dividers>
          <AddCameraForm
            onSubmit={handleSubmit}
            onCancel={handleClose}
            isLoading={isLoading}
            error={error}
          />
        </DialogContent>
      </Dialog>

      <Snackbar
        open={!!successMessage}
        autoHideDuration={3000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity="success"
          variant="filled"
        >
          {successMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default AddCameraModal;
