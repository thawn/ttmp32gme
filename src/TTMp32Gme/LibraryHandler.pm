package TTMp32Gme::LibraryHandler;

use strict;
use warnings;

use File::Basename qw(basename dirname);
use Data::Dumper;
use Path::Class;
use List::MoreUtils qw(uniq);

use Music::Tag ( traditional => 1 );
use Music::Tag::MusicBrainz;
use Music::Tag::MP3;
use Music::Tag::OGG;

#use Music::Tag:Amazon; #needs developer key
#use Music::Tag:LyricsFetcher; #maybe use this in a future release?

use TTMp32Gme::Build::FileHandler;

require Exporter;
our @ISA    = qw(Exporter);
our @EXPORT = qw(createLibraryEntry);

sub newOID {
	my $dbh = $_[0];
	my $oid;
	my @old_oids =
		@{ $dbh->selectall_arrayref('SELECT oid FROM gme_library ORDER BY oid DESC')
		};
	if (@old_oids) {
		if ( $old_oids[0] lt 999 ) {

			#if we have free oids above the highest used oid, then use those
			$oid = $old_oids[0] + 1;
		} else {

			#if oid 999 is already in the database,
			#then look for oids freed by deleting old ones
			my %oid_test = map { $_ => 1 } @old_oids;
			my $new_oid = $old_oids[-1] + 1;
			while ( $new_oid lt 1001 and $oid_test{$new_oid} ) {
				$new_oid++;
			}
			if ( $new_oid eq 1000 ) {

				#we still have not found a free oid,
				#look for free oids below the default oid
				$new_oid = $old_oids[-1] - 1;
				while ( $new_oid gt 0 and $oid_test{$new_oid} ) {
					$new_oid -= 1;
				}
				if ( $new_oid gt 1 ) {
					$oid = $new_oid;
				} else {
					error(
						'could not find a free oid.'
							. ' Try deleting oids from your library.',
						1
					);
				}
			} else {
				$oid = $new_oid;
			}
		}
	} else {
		$oid = 920;
	}
	return $oid;
}

sub createLibraryEntry {
	my ( $albumList, $dbh ) = @_;
	foreach my $album ( @{$albumList} ) {
		if ($album) {
			my $oid = newOID($dbh);
			my %albumData;
			my @trackData;
			my $pictureData;
			foreach my $fileId ( sort keys %{$album} ) {
				if ( $album->{$fileId} =~ /\.(mp3|ogg)$/i ) {

					#handle mp3 and ogg audio files
					my $info = Music::Tag->new( $album->{$fileId} );
					$info->get_tag( $album->{$fileId} );

					#fill in album info
					if ( !$albumData{'album_title'} && $info->album() ) {
						$albumData{'album_title'} = $info->album();
						$albumData{'path'}        = $albumData{'album_title'};
					}
					if ( !$albumData{'album_artist'} && $info->albumartist() ) {
						$albumData{'album_artist'} = $info->albumartist();
					} elsif ( !$albumData{'album_artist'} && $info->artist() ) {
						$albumData{'album_artist'} = $info->artist();
					}
					if ( !$albumData{'year'} && $info->year() ) {
						$albumData{'year'} = $info->get_year();
					}
					if ( !$albumData{'picture_filename'} && $info->picture_exists() ) {
						if ( $info->picture_filename() ) {
							$albumData{'picture_filename'} = $info->picture_filename();
						} elsif ( $info->picture() ) {
							my %pic = $info->picture();
							$pictureData = $pic{'_Data'};
							my $pictureName = basename( $pic{'filename'} );
							my $picturePath =
								( file( dirname( $album->{$fileId} ), $pictureName ) )
								->stringify;
							if ( !-e $picturePath ) {
								open( my $fh, '>', $picturePath );
								print $fh $pictureData;
								close($fh);
							}
							$albumData{'picture_filename'} = $picturePath;
						}
					}

					#fill in track info
					my %trackInfo = (
						'parent_oid' => $oid,
						'album'      => $info->album(),
						'artist'     => $info->artist(),
						'disc'       => $info->disc(),
						'duration'   => $info->duration(),
						'genre'      => $info->genre(),
						'lyrics'     => $info->lyrics(),
						'title'      => $info->title(),
						'track'      => $info->track(),
						'filename'   => $album->{$fileId},
					);
					push( @trackData, \%trackInfo );
				} elsif ( $album->{$fileId} =~ /\.(jpg|jpeg|tif|tiff|png|gif)$/i ) {

					#handle pictures
					open( my $file, '<', $album->{$fileId} );
					$pictureData = join( "", <$file> );
					close($file);
					$albumData{'picture_filename'} = basename( $album->{$fileId} );
				}
			}
			$albumData{'oid'} = $oid;
			if ( !$albumData{'album_title'} ) {
				$albumData{'path'}        = 'unknown';
				$albumData{'album_title'} = $albumData{'path'};
			}
			$albumData{'path'} = makeNewAlbumDir( $albumData{'path'} );
			if ( $albumData{'picture_filename'} ) {
				 $albumData{'picture_filename'} = moveToAlbum($albumData{'path'}, $albumData{'picture_filename'});
			}
			for my $track (@trackData) {
				$track->{'filename'} = moveToAlbum($albumData{'path'}, $track->{'filename'});
			}

			print Dumper( \%albumData );
			print Dumper( \@trackData );
		}
	}
	removeTempDir();
}

1;
